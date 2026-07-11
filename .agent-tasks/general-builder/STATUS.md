# General-Builder: Terraform Validation Fixes

## Task
Fix Terraform validation errors in `terraform/` directory — 3 categories of issues.

## Files Modified

| File | Change |
|------|--------|
| `terraform/outputs.tf` | All 13 outputs: replaced root-level resource refs (`aws_s3_bucket.input.id`, etc.) with module output refs (`module.input_bucket.bucket_id`, etc.) |
| `terraform/main.tf` | No semantic change needed (already used correct direct-attribute syntax). `terraform fmt` cleaned alignment spacing on line 9. |
| `terraform/env/dev.tfvars` | `terraform fmt` applied (whitespace only). |

## Module Audit Results

All modules were already correctly configured:

| Module | Variables? | Outputs? | Status |
|--------|-----------|----------|--------|
| `modules/s3-input/` | `project_name`, `environment`, `dashboard_origin` ✅ | `bucket_id`, `bucket_arn` ✅ | No changes needed |
| `modules/s3-output/` | `project_name`, `environment` ✅ | `bucket_id`, `bucket_arn` ✅ | No changes needed |
| `modules/sqs/` | `project_name`, `environment` ✅ | `queue_id`, `queue_arn`, `dlq_arn` ✅ | No changes needed |
| `modules/dynamodb/` | `project_name`, `environment` ✅ | `table_name`, `table_arn` ✅ | No changes needed |
| `modules/iam/` | `project_name`, `environment`, `input_bucket_arn`, `output_bucket_arn`, `queue_arn`, `table_arn` ✅ | `worker_role_arn`, `frontend_role_arn` ✅ | Already uses `var.*` refs in policies ✅ |

## Validation Result

```
terraform validate
Success! The configuration is valid.
```
