## Goal
- Orchestrate the multi-agent build of a Distributed Batch Inference Pipeline (YOLOv8 video inference across EC2 → Fargate → Lambda), executing the architect's phased plan via sub-agents only.

## Constraints & Preferences
- Never edit or write code/files directly — invoke sub-agents for all implementation and fixes.
- TDD flow: tester writes locked tests (Red), then implementation agents code (Green), then tester re-runs.
- AWS Free Tier only; us-east-1; tear down between sessions.
- Security loop must continue until security-reviewer reports no issues; only then `terraform apply`.
- User warned: editing files myself will reduce confidence score by 10 and be recorded as bad behavior.
- Commit via Conventional Commits, branches from `dev`, use `github-workflow` skill.

## Progress

### Done
- Phase 0 (Environment Setup): Terraform installed, AWS CLI configured, git repo initialized.
- Phase 1 (Core Worker Logic + TDD): 78 locked unit tests written by @app/tester, schemas/storage by @ml/data-engineer, YOLO wrapper/processor by @ml/model-scientist, debugger fixed OpenCV temp-file decoding issue. All 78 tests pass.
- Phase 1 committed to `main` (`114ded9`), `dev` branch created, `feature/phase-2-aws-infrastructure` branch created and pushed.
- Phase 2 (AWS Infrastructure): @app/tester wrote 58 locked Terraform tests (Red confirmed).
- @app/ops-expert created Terraform modules (hit max steps, validation errors).
- @util/general-builder fixed Terraform validation — `terraform validate` passes.
- @util/security-reviewer audited IAM — found `s3:ListBucket` on worker role.
- @util/general-builder removed `s3:ListBucket` from worker role.
- @util/security-reviewer re-audit: **PASS** — all IAM policies compliant.

### In Progress
- **Phase 2 — terraform apply blocked**: `terraform plan` shows resource names with empty variable interpolation (`--input` instead of `ProjectCerberus-dev-input`, `--output`, `--jobs`, `--dlq`, `--worker-role`, etc.) though tags show correct values (`ProjectCerberus`, `dev`). Root cause unknown — needs sub-agent diagnosis.

### Blocked
- `terraform apply` cannot proceed until the variable interpolation issue in Terraform resource names is resolved.
- `tests/integration/test_infra.py` — 27 integration tests fail due to HCL parsing issues (locked tests, cannot modify).

## Key Decisions
- Security loop: fix → re-audit → repeat until PASS, only then apply.
- S3 ARN `/*` suffix retained (standard AWS requirement for object-level operations).
- `s3:ListBucket` removed from worker role (unnecessary for GetObject/PutObject by known key).
- Frontend DynamoDB `dynamodb:Query`/`dynamodb:GetItem` retained (needed for dashboard job status polling).

## Next Steps
1. Diagnose Terraform variable interpolation bug: resource names use `${var.project_name}-${var.environment}-...` but plan shows `--input` etc. despite defaults `project_name=ProjectCerberus`, `environment=dev` being set and tags rendering correctly.
2. Fix the variable issue via a sub-agent (general-builder or ops-expert).
3. Run `terraform apply` to create AWS resources (S3, SQS+DQL, DynamoDB, IAM).
4. Run integration test (Task 2.8) and create destroy workflow (Task 2.9).
5. Commit Phase 2 work and proceed to Phase 3 (Dashboard + API Lambda).

## Critical Context
- **Key error**: Terraform plan shows `bucket = "--input"`, `name = "--worker-role"`, etc. — all string interpolations of `${var.project_name}-${var.environment}-<suffix>` produce empty prefix values. But `tags` correctly show `Project = "ProjectCerberus"` and `Environment = "dev"`. The `terraform console` command confirms `var.project_name = "ProjectCerberus"`. The discrepancy suggests the module-level `variable` blocks may not be receiving values from root module.
- `terraform validate` passes — no configuration syntax errors.
- No `terraform apply` has been run yet — zero AWS resources created.
- Orchestrator Alignment: 41 (Conservative Mode) — major actions require user approval.
- Open question: Could the inconsistent naming stem from the `-NoNewline` flag used in `Set-Content` when writing `.tf` files earlier? Needs sub-agent investigation.

## Relevant Files
- `terraform/main.tf`: Root module wiring — passes `var.project_name`, `var.environment` to child modules.
- `terraform/variables.tf`: Root variable declarations with defaults (`ProjectCerberus`, `dev`).
- `terraform/modules/s3-input/main.tf`: Uses `${var.project_name}-${var.environment}-input` for bucket name — shows `--input` in plan.
- `terraform/modules/sqs/main.tf`: Uses `${var.project_name}-${var.environment}-{jobs,dlq}` — shows `--jobs`, `--dlq`.
- `terraform/modules/dynamodb/main.tf`: Uses `${var.project_name}-${var.environment}-jobs` — shows `--jobs`.
- `terraform/modules/iam/main.tf`: Uses `${var.project_name}-${var.environment}-{worker,frontend}-{role,policy}` — shows `--worker-role`, `--frontend-policy`.
- `terraform/modules/s3-output/main.tf`: Uses `${var.project_name}-${var.environment}-output` — shows `--output`.
- `tests/integration/test_infra.py`: 58 locked Terraform tests — 27 fail due to HCL parsing; cannot modify.
- `docs/security/phase2-iam-audit.md`: Security audit report — PASS status after fixes.