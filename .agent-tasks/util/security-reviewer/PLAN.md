# PLAN — @util/security-reviewer

**Role**: Read-only IAM permissions audit. No source code modification.

## Tasks

### 2.10 — Phase 2 IAM audit

Review Terraform IAM modules for:
- S3: worker role should have `s3:GetObject` on input bucket, `s3:PutObject` on output bucket — NOT `s3:*` on all buckets
- SQS: worker role should have `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes` — NOT `sqs:*`
- DynamoDB: worker role should have `dynamodb:PutItem`, `dynamodb:UpdateItem`, `dynamodb:GetItem` — NOT `dynamodb:*`
- Dashboard/API role should have `s3:PutObject` (for uploads) and `sqs:SendMessage` only
- No wildcard `Action: "*"` on any role
- No `Resource: "*"` without justification

### 6.7 — Phase 6 Lambda IAM audit

Review Lambda IAM:
- Lambda execution role follows same least-privilege pattern
- Lambda should NOT have `s3:ListBucket` or `s3:DeleteObject`
- SQS trigger permissions correct (event-source mapping)
- Verify Lambda cannot access other AWS services it doesn't need (no `ec2:*`, no `dynamodb:DeleteTable`, etc.)

## Output

Each audit produces a report file:

```
docs/security/
  phase2-iam-audit.md
  phase6-lambda-audit.md
```
