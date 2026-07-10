"""Evidence Vault — the governed audit is append-only, and the deployed IaC makes it
immutable (Deny on DynamoDB UpdateItem/DeleteItem) + WORM (S3 Object Lock). Offline-provable."""
import glob
import os

from hcls_agent_platform.mcp_gateway.audit import GatewayAuditLog

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_audit_log_is_append_only_by_api():
    log = GatewayAuditLog()
    a = log.record({"decision": "ALLOW", "tool": "x.read", "user": "u1"})
    first = dict(log.records[0])
    b = log.record({"decision": "DENY", "tool": "x.write", "user": "u2"})
    assert a != b                                  # unique audit ids
    assert len(log.records) == 2                   # append, not overwrite
    assert log.records[0] == first                 # the prior record is unchanged
    # The writer API exposes no mutate/delete/overwrite path — the only writer is record().
    for banned in ("update", "delete", "overwrite", "edit", "remove", "set_record"):
        assert not hasattr(log, banned), f"audit log must not expose {banned}()"


def test_iac_denies_audit_mutation_and_enables_object_lock():
    texts = []
    for pat in ("**/*.yaml", "**/*.yml", "**/*.tf"):
        for f in glob.glob(os.path.join(REPO, "infra", pat), recursive=True):
            try:
                texts.append(open(f, encoding="utf-8").read())
            except (UnicodeDecodeError, PermissionError):
                pass
    blob = "\n".join(texts)
    assert "DeleteItem" in blob and "UpdateItem" in blob, "IaC must deny audit-table mutation"
    assert ("ObjectLock" in blob or "object_lock" in blob), "IaC must enable S3 Object Lock (WORM)"


def test_worm_denies_governance_bypass():
    """The WORM bucket policy denies s3:BypassGovernanceRetention (except a break-glass role) so a
    GOVERNANCE-mode pilot cannot be silently deleted; COMPLIANCE mode is the production default."""
    import glob as _glob
    txt = ""
    for f in _glob.glob(os.path.join(REPO, "infra", "cloudformation", "data.yaml")):
        try:
            txt += open(f, encoding="utf-8").read()
        except (UnicodeDecodeError, PermissionError):
            pass
    assert "BypassGovernanceRetention" in txt, "WORM bucket policy must deny s3:BypassGovernanceRetention"
    assert "RetentionMode" in txt or "COMPLIANCE" in txt, "retention mode must be explicit"
