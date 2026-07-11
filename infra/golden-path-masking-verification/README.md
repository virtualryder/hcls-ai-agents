# Golden path — runtime PII/PHI masking verification (Comprehend Medical + Comprehend)

Deployable proof that the Aegis **NER masking control runs on AWS, fail-closed, and masks before the
audit write**. It wires **Amazon Comprehend Medical `DetectPHI`** (PHI) and **Amazon Comprehend
`DetectPiiEntities`** (general PII) into a deployed Lambda that reads a record from S3, redacts every
detected entity, and writes only the masked text to an append-only audit table.

This is the runtime evidence for the control the maturity scorecard marks `implemented` /
"not-runtime-verified." See [`EVIDENCE.md`](EVIDENCE.md) for a captured live run.

> **Scope:** verification/reference stack on **synthetic** data. Not for real regulated data as-is —
> a customer wires this into the hero pipeline and tunes the regex ID pass to their MRN/account formats.

## What it deploys
`template.yaml` (cfn-lint clean, pseudo-parameterized for account/partition):
KMS CMK · S3 bucket (SSE-KMS, public access blocked) · append-only DynamoDB audit table
(PITR, IAM `Deny` on Update/Delete) · least-privilege IAM role · the masking Lambda.
`comprehendmedical:DetectPHI` / `comprehend:DetectPiiEntities` do not support resource-level IAM, so
those actions are scoped `"*"` (the required, expected scope); everything else is tightly scoped.

## Run it (≈ 3 min, a few cents)
```bash
ACCOUNT=$(aws sts get-caller-identity --query Account --output text); REGION=us-east-1
aws cloudformation create-stack --stack-name aegis-masking-verify --region "$REGION" \
  --template-body file://template.yaml --capabilities CAPABILITY_NAMED_IAM
aws cloudformation wait stack-create-complete --stack-name aegis-masking-verify --region "$REGION"

BUCKET=$(aws cloudformation describe-stacks --stack-name aegis-masking-verify --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='DataBucketName'].OutputValue" --output text)
aws s3 cp synthetic_phi_record.txt "s3://$BUCKET/synthetic_phi_record.txt" --region "$REGION"

aws lambda invoke --function-name aegis-masking-verify --region "$REGION" \
  --cli-binary-format raw-in-base64-out --payload '{"s3_key":"synthetic_phi_record.txt"}' out.json
cat out.json   # phi_types / pii_types detected, masked_text, masked_before_persist=true

# teardown (empty bucket first)
aws s3 rm "s3://$BUCKET" --recursive --region "$REGION"
aws cloudformation delete-stack --stack-name aegis-masking-verify --region "$REGION"
```

## Applying it to the other packs
- **PHI (hcls, healthcare/HPP):** `DetectPHI` as above.
- **General PII (edu, slg):** the same Lambda already runs `DetectPiiEntities`; drop the `DetectPHI`
  call (or keep both) and tune the regex ID pass for student-id / case-id formats.
