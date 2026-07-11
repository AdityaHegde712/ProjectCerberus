# Test Plan — Native Terraform `.tftest.hcl` for Phase 2

## Approach

Replace Python/pytest integration tests (`tests/integration/test_infra.py`) with
native Terraform `.tftest.hcl` files that run via `terraform test`.

## Test Strategy

- **Mode**: All tests use `command = plan` with `mock_provider "aws" {}` — fast, no real
  AWS calls, no credentials needed, suitable for CI.
- **Coverage**: Schema/attribute assertions for every resource, IAM least-privilege
  checks, cross-resource wiring verification, root output validation.
- **Gaps**: Runtime behavior (end-to-end message processing) can't be tested by
  native `terraform test` — documented in output.

## File Layout

| File | Scope |
|------|-------|
| `tests/s3.tftest.hcl` | Input bucket (name, versioning, encryption, CORS, tags) + Output bucket (name, encryption, tags) |
| `tests/messaging.tftest.hcl` | SQS queues (name, visibility timeout, wait time, redrive policy, DLQ retention, tags) + DynamoDB table (name, billing mode, hash key, TTL, tags) |
| `tests/iam.tftest.hcl` | IAM roles (trust policies, naming, tags), IAM policies (actions per role, no wildcard actions, no wildcard resources), role-policy attachments |
| `tests/root_module.tftest.hcl` | Root module outputs (11 outputs defined), cross-module wiring (IAM receives ARN inputs), variable defaults |

## Requirement-to-Assertion Mapping

See coverage table in final output.

## Files to Create

- `terraform/tests/s3.tftest.hcl`
- `terraform/tests/messaging.tftest.hcl`
- `terraform/tests/iam.tftest.hcl`
- `terraform/tests/root_module.tftest.hcl`
