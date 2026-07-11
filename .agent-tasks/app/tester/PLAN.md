# PLAN — @app/tester

**Role**: Test specialist. Writes [LOCKED] tests before implementation code. Enforces Red-Green-Refactor.

## Task List

| Task ID | Description | Phase | Complexity | Locked |
|---|---|---|---|---|
| 1.1 | Unit tests for JobInput/JobResult/Detection schemas (Pydantic) | 1 | 4 | Yes |
| 1.3 | Unit tests for YOLO wrapper abstraction | 1 | 5 | Yes |
| 1.5 | Unit tests for S3 storage adapter (local file mock) | 1 | 5 | Yes |
| 1.7 | Unit tests for `process_video()` function | 1 | 6 | Yes |
| 1.9 | Run full Phase 1 test suite + code coverage | 1 | 2 | No |
| 2.1 | Tests for Terraform module outputs | 2 | 4 | Yes |
| 3.2 | Component tests for UploadForm | 3 | 4 | Yes |
| 3.4 | Component tests for JobStatusList | 3 | 4 | Yes |
| 3.6 | Component tests for ResultViewer | 3 | 5 | Yes |
| 3.10 | E2E test: upload → SQS → process → result visible | 3 | 4 | No |
| 4.3 | E2E test for EC2 worker path | 4 | 6 | Yes |
| 5.6 | Integration test for Fargate path | 5 | 6 | Yes |
| 6.5 | Integration test for Lambda path | 6 | 7 | Yes |

## Testing Approach

- **Unit tests**: pytest with mocking (local filesystem for S3, mock YOLO model)
- **Component tests**: React Testing Library for dashboard components
- **Integration tests**: `pytest` with `boto3` against real AWS resources (tagged `integration`)
- **E2E tests**: Full pipeline from upload to result verification
- **Pattern**: Write ALL locked tests for a phase first → confirm all fail (Red) → signal orchestrator → wait for implementation → re-run tests → report pass/fail

## TDD Workflow

All [LOCKED] tests follow this protocol. Tester does NOT modify implementation code:

1. **Write all locked tests** for a phase (e.g., all Phase 1 unit tests)
2. **Run full test suite** → confirm ALL tests fail (Red) because no implementation exists
3. **Signal orchestrator**: "All Phase X locked tests written. All fail as expected. Awaiting implementation."
4. **Wait** for orchestrator to dispatch implementation agents
5. **Re-run tests** after implementation agents signal completion
6. **Report results**: which tests pass, which fail, any unexpected behavior
7. If tests fail → signal orchestrator with failure details. Do NOT fix implementation.

## Test Directory Structure

```
tests/
  unit/
    test_schemas.py      (1.1)
    test_detector.py     (1.3)
    test_storage.py      (1.5)
    test_processor.py    (1.7)
  integration/
    test_infra.py        (2.1)
    test_ec2_path.py     (4.3)
    test_fargate_path.py (5.6)
    test_lambda_path.py  (6.5)
  component/
    test_upload_form.py  (3.2)
    test_job_status.py   (3.4)
    test_result_viewer.py(3.6)
  e2e/
    test_pipeline.py     (3.10)
```
