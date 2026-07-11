# STATUS — @app/tester

**Date**: 2026-07-10 17:47
**Phase**: 2 — Red step (all tests fail)
**Status**: All 4 Phase 1 + 1 Phase 2 locked test files written, confirmed failing. Awaiting implementation.

## Completed

| Task ID | File | Status |
|---------|------|--------|
| 1.1 | `tests/unit/test_schemas.py` | 🔴 RED — Written, fails (no impl) |
| 1.3 | `tests/unit/test_detector.py` | 🔴 RED — Written, fails (no impl) |
| 1.5 | `tests/unit/test_storage.py` | 🔴 RED — Written, fails (no impl) |
| 1.7 | `tests/unit/test_processor.py` | 🔴 RED — Written, fails (no impl) |
| 2.1 | `tests/integration/test_infra.py` | 🔴 RED — Written, 58 failures confirmed (no TF files) |

## Infrastructure Created

| File | Purpose |
|------|---------|
| `tests/__init__.py` | Test package marker |
| `tests/unit/__init__.py` | Unit test package marker |
| `tests/integration/__init__.py` | Integration test package marker |
| `tests/integration/test_infra.py` | Phase 2 Terraform module output tests (58 tests) |
| `pyproject.toml` | Project config with pytest + dev deps |

## Recent Test Results (Phase 2)

```
$ pytest tests/integration/test_infra.py -v --tb=short
=================================== FAILURES ===================================
58 failed in 0.98s
```

All failures are due to missing Terraform files (expected — Red phase).

## Handover Notes

### Phase 1 implementation agents (`@ml/data-engineer`, `@ml/model-scientist`)
- Implement: `worker/src/schemas.py`, `detector.py`, `storage.py`, `processor.py`
- All Phase 1 tests are [LOCKED]. Do NOT modify test files.

### Phase 2 implementation agent (`@app/ops-expert`)
- Implement Terraform modules at `terraform/`:
  - `terraform/main.tf` — Root module wiring all sub-modules
  - `terraform/variables.tf` — Input variables (environment, project_name, dashboard_origin)
  - `terraform/outputs.tf` — All 11 required outputs (see test class `TestTerraformRoot`)
  - `terraform/modules/s3-input/main.tf` — Input bucket with CORS, versioning, encryption
  - `terraform/modules/s3-output/main.tf` — Output bucket with encryption, private ACL
  - `terraform/modules/sqs/main.tf` — Standard queue + DLQ with redrive_policy
  - `terraform/modules/dynamodb/main.tf` — Table with jobId PK, TTL, PAY_PER_REQUEST
  - `terraform/modules/iam/main.tf` — Worker + Frontend roles with least-privilege policies
- All Phase 2 tests are [LOCKED]. Do NOT modify test files.
- Run `python -m pytest tests/integration/test_infra.py --tb=short` to verify progress.
