# Runtime PII/PHI masking — live AWS evidence

**What this proves:** the NER masking control **executes on AWS, fail-closed, and masks before the
audit write** — using Amazon **Comprehend Medical `DetectPHI`** (PHI) and Amazon **Comprehend
`DetectPiiEntities`** (general PII). This closes the "masking never runtime-verified on AWS" gap.

- **Account / region:** `864217980669` / `us-east-1`  ·  **Date:** 2026-07-11
- **Stack:** `aegis-masking-verify` (this directory's `template.yaml`) — deployed, exercised, torn down.
- **Method:** a synthetic ICSR narrative (fake patient) was staged in the stack's S3 bucket, read by the
  Lambda, run through both NER engines, redacted, and the **masked-only** record written to an
  append-only DynamoDB audit table (conditional `PutItem`; IAM `Deny` on Update/Delete). Raw text was
  never persisted.

## Input (synthetic — not real patient data)
```
Patient: Jordan A. Fakepatient, DOB 1978-04-12, MRN 00-FAKE-4471, SSN 123-45-6789.
Contact: jordan.fake@example.org, phone (312) 555-0142, 200 Pretend Ave, Springfield, IL.
Treating clinician Dr. Robin Notreal at Anytown General Hospital advised discontinuation.
```

## Live result (Lambda return + audit row)
- **Comprehend Medical `DetectPHI`:** 7 entities — `ADDRESS, DATE, EMAIL, ID, NAME, PHONE_OR_FAX`
- **Comprehend `DetectPiiEntities`:** 7 entities — `ADDRESS, DATE_TIME, EMAIL, NAME, PHONE, SSN`
- **`masked_before_persist: true`**, `leak_detected: false`, `fail_closed: true`

```
Patient: [PHI:NAME], DOB [PHI:DATE], MRN 00-FAKE-4471, SSN [PHI:ID].
Contact: [PHI:EMAIL], phone [PHI:PHONE_OR_FAX], [PII:ADDRESS].
Treating clinician Dr. [PHI:NAME] at [PHI:ADDRESS] advised discontinuation.
```
The DynamoDB audit row (`AUD-1c47431c77e8b7556e87`) contains only the masked text plus the detected
entity-type lists and the engine identifier — the raw SSN, name, email, and phone are absent.

## Honest finding (why NER is necessary but not sufficient)
`MRN 00-FAKE-4471` was **not** masked — the free-text NER models don't recognize that site-specific
MRN format. This is exactly why the Aegis masker keeps a **regex Safe-Harbor pass for structured
identifiers (SSN/MRN/account numbers) alongside NER**: regex catches deterministic ID formats; NER
catches the free-text names, addresses, and dates regex cannot. Neither alone is complete; the control
runs both and fails closed. For real regulated data a customer tunes the regex ID patterns to their
site's MRN/account formats during the pilot. This is disclosed, not hidden.

## Fail-closed
`FAIL_CLOSED=1` (default): if either NER call errors, the handler raises and **no audit record is
written** — the pipeline blocks rather than persisting under-masked data.

## Reproduce
See `README.md` — one deploy, one upload, one invoke, one teardown. Cost is a few cents
(Comprehend/Comprehend Medical per-unit + trivial S3/DynamoDB/KMS).
