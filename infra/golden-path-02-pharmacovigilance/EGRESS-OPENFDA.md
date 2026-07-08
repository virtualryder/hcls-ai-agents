# Controlled egress for the openFDA real connector (A6)

**The problem.** `SafetySource=openfda` makes Agent 02 read real FAERS data from
`https://api.fda.gov`. That is a **public, non-AWS** endpoint, so it can't be reached over a
PrivateLink/VPC endpoint — it needs real internet egress. A VPC-attached connector Lambda has **no
internet egress by default** (the network stack only opens VPC endpoints to AWS services). That's the
correct fail-closed posture: the agent can't call arbitrary endpoints.

**The control.** `egress-openfda.yaml` provisions an **AWS Network Firewall** whose stateful policy
**allows TLS/HTTP to `api.fda.gov` only** (ALLOWLIST on `TLS_SNI` + `HTTP_HOST`) and **drops
everything else** (`aws:drop_established`, STRICT_ORDER). Every denied attempt is logged to CloudWatch
— so you have proof the allow-list holds. This is the concrete answer to *"how do you stop the agent
from exfiltrating to an arbitrary host?"*: it physically can't reach anything but the one approved
data source.

## Deploy

1. **Golden path with the real source** (functions VPC-attached to the connector subnet):
   ```bash
   sam deploy --stack-name hcls-02-dev \
     --parameter-overrides ConnectorMode=live SafetySource=openfda \
       VpcSubnetIds=<connector-private-subnets> VpcSecurityGroupId=<app-sg> ...
   ```
2. **Egress firewall** (same VPC, a dedicated firewall subnet per AZ):
   ```bash
   aws cloudformation deploy --template-file egress-openfda.yaml \
     --stack-name hcls-02-dev-egress \
     --parameter-overrides VpcId=<vpc-id> FirewallSubnetIds=<fw-subnet-a>,<fw-subnet-b>
   ```
3. **Route** the connector subnet's `0.0.0.0/0` to the **firewall endpoint** (from the firewall's
   `SubnetMappings` / VPC-endpoint id), and the firewall subnet's `0.0.0.0/0` to **NAT → IGW**. Now
   all connector egress passes through the allow-list.

## Verify the control

- **Allowed:** the connector reaches `api.fda.gov` → `safety.get_case` returns real FAERS data.
- **Denied:** any other host (e.g., a test `curl https://example.com`) is dropped by the firewall and
  appears in the `FirewallLogGroup` ALERT log. That log is the evidence for the assurance packet.

## Scope / honesty

- Reads only. `write_case_draft` / `submit_report` stay human-gated and go to the customer's validated
  safety system, not openFDA.
- The same pattern (allow-list one FQDN, deny the rest) is how you'd govern egress to *any* approved
  external source. For the **PHI-under-BAA** variant, swap to AWS HealthLake FHIR (an AWS service
  reached over PrivateLink — no firewall needed, and no BAA-covered data ever traverses the public
  internet).
- Network Firewall is a real cost line (~$0.395/hr per endpoint + data processing); for a short pilot
  it's a few dollars. For a low-cost pilot without a firewall, run the connector **without** VPC
  attachment (Lambda-managed network has egress) and accept that egress isn't FQDN-restricted — but
  the firewall is the defensible production control and the one to show a CISO.
