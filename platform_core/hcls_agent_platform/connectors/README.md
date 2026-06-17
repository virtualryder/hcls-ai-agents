# Connector Framework

A connector is the typed adapter to a system of record. Agents never call a
vendor SDK directly — they call the MCP gateway, which (after authorizing) calls
a connector method. Method names match `mcp_gateway/policy.py:TOOL_REGISTRY`.

## Modes

| Mode | When | Backing store |
|---|---|---|
| `fixture` (default) | demos, CI, governance evals | deterministic offline data, no PHI |
| `live` | production engagement | validated vendor clients (`live.py`) |

Set with `CONNECTOR_MODE=fixture|live`. Fixture mode runs the whole suite with no
AWS account and no credentials.

## Systems covered

| `kind` | System of record | Representative vendors |
|---|---|---|
| `rim` | Regulatory information management | Veeva Vault RIM |
| `dms` | Document / content management | Veeva Vault, OpenText |
| `safety` | Pharmacovigilance / ICSR | Oracle Argus, Veeva Safety, ArisGlobal |
| `meddra` / `whodrug` | Medical coding dictionaries | MedDRA MSSO, UMC WHODrug |
| `edc` | Electronic data capture | Medidata Rave, Veeva CDMS |
| `ctms` / `etmf` | Trial management / trial master file | Veeva Vault Clinical |
| `rwd` | Real-world / claims data | clean rooms, registries |
| `qms` | Quality management | Veeva QMS, MasterControl |
| `crm` / `mlr` | Commercial / medical, promotional review | Veeva/Salesforce CRM |

## Adding a live integration

1. Implement the method on a typed subclass in `live.py`, wrapping the validated
   vendor client. Preserve the fixture method signature exactly.
2. Resolve credentials via `hcls_agent_platform.secrets.get_secret`.
3. Register the connector in `factory.py`.
4. The call still flows through the gateway: authorize → mint scoped token →
   invoke → audit. Live calls run inside the short-lived token — no standing
   service account into a regulated system.
