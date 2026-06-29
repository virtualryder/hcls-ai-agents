# Reviewer service (round-2 #2)

The authenticated human-approval API that replaces the smoke-test `mint_approval.py` stand-in.

## What it closes
- **Authenticated reviewer** — identity comes from the Cognito JWT (federated Okta/Entra), via the
  HTTP API JWT authorizer; never from the request body.
- **Role authorization** — `build_review_decision` rejects any caller whose `custom:hcls_role` is not
  entitled to approve (`DEFAULT_APPROVER_ROLES`).
- **Identity attribution + e-signature** — the bound approval token is minted **server-side** with
  `approver = authenticated sub`, so the signature is attributable to a unique individual and bound to
  the exact action (agent + tool + args), single-use and time-limited.
- **Separation of duties** — `sub == requestor` is refused.
- **Controlled rejection** — a non-approve decision resumes the workflow via `SendTaskFailure`.

## Flow
1. `hitl_notify` writes the pending record (task token + `approval_binding`) keyed by `approval_id`.
2. Reviewer signs in (federated) and `POST /approvals/{approval_id}` with `{"decision":"approved"}`.
3. Service loads the pending record, authorizes the role, mints the bound token, and calls
   `SendTaskSuccess` with `{approved, reviewer, approval_token}` → `finalize` verifies and submits.

## Status
Reference scaffold. The pure decision/minting core is unit-tested
(`platform_core/tests/test_reviewer_service.py`); cfn-lint validates the template. Federated login,
role assertion from a real IdP, and the Step Functions callback require a live-account run (the
clean-account acceptance test). A reviewer **UI** (session timeout, reassignment, acknowledgement
text) is the remaining product surface.
