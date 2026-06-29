# Customer IdP Federation Runbook (F6)

How to federate the HCLS Cognito user pool to a customer identity provider so that
**sign-in, group membership, and approver role** are owned by the customer's IdP —
no user accounts are managed in AWS. Covers **Okta** and **Microsoft Entra ID**
(Azure AD), the claim→role mapping the gateway authorizer depends on, and how to
flip federation on/off.

> **What the templates do.** `infra/cloudformation/security.yaml` provisions:
> an `AWS::Cognito::UserPoolIdentityProvider` (SAML), an `AWS::Cognito::UserPoolDomain`
> (hosted UI), and federated wiring on the `AWS::Cognito::UserPoolClient`
> (`SupportedIdentityProviders`, `AllowedOAuthFlows: [code]`, scopes, callback/logout
> URLs). All of it is gated by the CloudFormation Condition **`FederationEnabled`**,
> which is true only when `IdpMetadataUrl` is non-empty. With an empty
> `IdpMetadataUrl` (the dev default) the pool stays native Cognito and nothing
> federated is created — dev deploys unchanged.

---

## 0. The contract the platform depends on

The gateway authorizer decides *who may approve* a regulated action from a single
custom claim: **`custom:hcls_role`**. Federation must map the IdP's group/role
claim into that attribute. The `email` claim is also mapped for audit identity.

| Cognito attribute   | Sourced from IdP claim                | Used for |
|---------------------|----------------------------------------|----------|
| `email`             | the IdP email/UPN claim                | audit identity, separation-of-duties (requester ≠ approver) |
| `custom:hcls_role`  | the IdP **group/role** claim           | authorization (e.g. `PV_MEDICAL_REVIEWER` may approve an ICSR draft) |

The mapping is set in `security.yaml` (`AttributeMapping`) for the common SAML
claim URIs and can be overridden in the Cognito console per IdP if the customer
emits non-standard claim names.

---

## 1. Stack parameters

Pass these to the quickstart (or `security.yaml` directly):

| Parameter              | Example                                                        | Notes |
|------------------------|----------------------------------------------------------------|-------|
| `IdpMetadataUrl`       | `https://<tenant>.okta.com/app/<id>/sso/saml/metadata`         | **Non-empty turns federation ON.** Empty = native Cognito. |
| `CallbackUrl`          | `https://reviewer.acme.example/callback`                       | OAuth redirect URL registered on the app client (and used as logout URL). |
| `UserPoolDomainPrefix` | `acme-hcls-prod`                                               | Hosted-UI domain label; globally unique per region. Required when federation is on. |

`scripts/deploy.sh` passes these through from the environment variables
`IDP_METADATA_URL`, `CALLBACK_URL`, `USER_POOL_DOMAIN_PREFIX`.

---

## 2. Okta (SAML)

1. **Okta Admin → Applications → Create App Integration → SAML 2.0.**
2. **Single sign-on URL / Audience (SP entity ID).** You need the Cognito values,
   which depend on the hosted-UI domain you chose:
   - **ACS URL:** `https://<UserPoolDomainPrefix>.auth.<region>.amazoncognito.com/saml2/idpresponse`
   - **Audience URI (SP entity ID):** `urn:amazon:cognito:sp:<UserPoolId>`
   (Get `<UserPoolId>` from the stack output `UserPoolId`; the domain from
   `HostedUiDomain`.)
3. **Attribute Statements** — emit at minimum:
   - `email` → `user.email`
   - a **group claim**: add a **Group Attribute Statement** named e.g. `Group`
     filtered to the PV reviewer groups (e.g. regex `GRP-PV-.*`).
4. **Assign** the relevant Okta groups (e.g. `GRP-PV-PHYSICIANS`) to the app.
5. **Copy the Okta IdP metadata URL** (Sign-On tab → *Identity Provider metadata*).
   This is your `IdpMetadataUrl`.
6. **Map the group → role.** In Cognito (or by editing `AttributeMapping` in
   `security.yaml`) map the SAML `Group` claim
   (`http://schemas.xmlsoap.org/claims/Group`) to `custom:hcls_role`. If your group
   names are not the literal role strings the policy expects, use an Okta
   **expression** in the attribute statement to emit the role string directly
   (e.g. `isMemberOfGroupName("GRP-PV-PHYSICIANS") ? "PV_MEDICAL_REVIEWER" : ""`).

---

## 3. Microsoft Entra ID (Azure AD) (SAML)

1. **Entra admin center → Enterprise applications → New application → Create your
   own application → "Integrate any other application (non-gallery)".**
2. **Single sign-on → SAML.** Set:
   - **Identifier (Entity ID):** `urn:amazon:cognito:sp:<UserPoolId>`
   - **Reply URL (ACS):** `https://<UserPoolDomainPrefix>.auth.<region>.amazoncognito.com/saml2/idpresponse`
3. **Attributes & Claims:**
   - Ensure `email` (or `user.mail` / `user.userprincipalname`) is emitted as the
     email claim.
   - Add a **group claim** (Token configuration → *groups claim* → "Groups assigned
     to the application"). Entra emits group **object IDs** by default; to emit
     names, either configure the app to surface group names or use a Cognito
     mapping that translates the known group GUID → role downstream.
4. **Users and groups:** assign the PV reviewer group to the application.
5. **App Federation Metadata URL** (on the SAML SSO page) → this is your
   `IdpMetadataUrl`.
6. **Map the group claim → `custom:hcls_role`** in Cognito, exactly as in §2.6.
   Because Entra emits GUIDs, the cleanest pattern is an **Entra claims-transformation**
   that emits the literal role string (e.g. `PV_MEDICAL_REVIEWER`) for members of
   the reviewer group, so `custom:hcls_role` carries the role directly.

---

## 4. OIDC alternative

OIDC is accepted instead of SAML. In `security.yaml` change the
`CustomerIdentityProvider` resource:

```yaml
ProviderType: OIDC
ProviderDetails:
  client_id: "<oidc-app-client-id>"
  client_secret: "<oidc-app-client-secret>"
  oidc_issuer: "https://<issuer>"
  attributes_request_method: GET
  authorize_scopes: "openid email profile groups"
AttributeMapping:
  email: email
  "custom:hcls_role": groups
```

`IdpMetadataUrl` still gates `FederationEnabled`; you can leave it non-empty (e.g.
the issuer's `.well-known` URL) to keep the condition on, or refactor the condition
to a dedicated `FederationEnabled` boolean parameter for OIDC-only deployments.

---

## 5. Flipping federation on / off

- **ON:** deploy with a non-empty `IdpMetadataUrl` (+ `UserPoolDomainPrefix` and a
  real `CallbackUrl`). The `FederationEnabled` condition provisions the IdP, the
  hosted-UI domain, and the federated app-client wiring. Stack output
  `FederationEnabled` reads `true` and `HostedUiDomain` shows the sign-in domain.
- **OFF (dev / native Cognito):** deploy with `IdpMetadataUrl=""` (default). No IdP,
  no domain, no OAuth callback URLs; the app client stays `SupportedIdentityProviders: [COGNITO]`.
- **Switching a live stack on** is a normal stack update — the new resources are
  additive and the app-client `!If` switches its provider list. Plan the cutover
  with the customer (existing native users vs. federated users).

---

## 6. Verify

1. Stack output `FederationEnabled == true`, `HostedUiDomain` set.
2. Navigate to the hosted UI:
   `https://<HostedUiDomain>.auth.<region>.amazoncognito.com/login?client_id=<UserPoolClientId>&response_type=code&scope=openid+email+profile&redirect_uri=<CallbackUrl>`
   → you should be redirected to the customer IdP, authenticate, and land back at
   `CallbackUrl` with a `code`.
3. Exchange the code for tokens and decode the ID token: confirm `email` and
   **`custom:hcls_role`** are present and correct. The gateway authorizer reads
   `custom:hcls_role`; an empty/wrong value = deny on approval.

> **Live-account note.** The end-to-end federated login (steps 2–3) and the
> claim→role assertion can only be confirmed against a real Cognito pool + IdP.
> This runbook + the cfn-lint-clean templates are validated structurally; the live
> federated-login leg is part of the P0 clean-account acceptance test.
