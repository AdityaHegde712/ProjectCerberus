# TASKS — Distributed Batch Inference Pipeline

**Complexity scale**: 1 (trivial) → 10 (extremely complex)  
**Status**: pending | in_progress | completed | blocked | cancelled  
**Locked**: Tasks marked "[LOCKED]" cannot be modified by implementation agents (test contracts).

---

## Phase 0: Environment Setup (Manual — Owner)

| # | Task | Complexity | Deps | Acceptance Criteria |
|---|---|---|---|---|
| 0.1 | Install Terraform | 2 | — | `terraform --version` succeeds |
| 0.2 | Configure AWS CLI (IAM user + access keys) | 3 | — | `aws sts get-caller-identity` returns valid JSON |
| 0.3 | Initialize git repo + push to GitHub | 2 | — | `git push -u origin main` succeeds |
| 0.4 | Run verification checklist | 1 | 0.1, 0.2, 0.3 | All tools report versions, AWS identity confirmed |

---

## Phase 1: Core Worker Logic + TDD

| # | Task | Role | Complexity | Deps | Acceptance Criteria |
|---|---|---|---|---|---|
| 1.1 | [LOCKED] Write unit tests for JobInput/JobResult/Detection schemas (Pydantic) | @app/tester | 4 | — | Tests validate field types, defaults, and serialization. Red step passes (tests fail before impl). |
| 1.2 | Implement data schema models in `worker/src/schemas.py` | @ml/data-engineer | 3 | 1.1 | Pydantic models pass all tests from 1.1. |
| 1.3 | [LOCKED] Write unit tests for YOLO wrapper abstraction | @app/tester | 5 | 1.2 | Tests verify mock model interface: `load_model()`, `predict(frame) -> List[Detection]`. Red step passes. |
| 1.4 | Implement YOLO wrapper in `worker/src/detector.py` | @ml/model-scientist | 4 | 1.3 | Wrapper loads ultralytics YOLOv8n, returns typed Detections. Tests pass. |
| 1.5 | [LOCKED] Write unit tests for S3 storage adapter (with local file mock) | @app/tester | 5 | 1.2 | Tests verify read/write with local filesystem mock. Red step passes. |
| 1.6 | Implement S3 storage adapter in `worker/src/storage.py` | @ml/data-engineer | 4 | 1.5 | Adapter handles local file fallback (no AWS) + S3 client. Tests pass. |
| 1.7 | [LOCKED] Write unit tests for `process_video()` function | @app/tester | 6 | 1.4, 1.6 | Tests verify: mock video → mock YOLO output → correct JobResult JSON. Edge cases: empty video, corrupt frames, no detections. Red step passes. |
| 1.8 | Implement `process_video()` in `worker/src/processor.py` | @ml/model-scientist | 5 | 1.7 | Function orchestrates: read frames → detect → write results. All tests pass. |
| 1.9 | Run full Phase 1 test suite + code coverage report | @app/tester | 2 | 1.2, 1.4, 1.6, 1.8 | All tests green, coverage > 80% on core modules. |

---

## Phase 2: AWS Infrastructure v1

| # | Task | Role | Complexity | Deps | Acceptance Criteria |
|---|---|---|---|---|---|
| 2.1 | [LOCKED] Write Terratest or shell-based tests for Terraform module outputs | @app/tester | 4 | — | Tests verify expected resource names, IAM policies, bucket configurations. |
| 2.2 | Create Terraform module: S3 input bucket with CORS policy | @app/ops-expert | 4 | 2.1 | Bucket created, CORS allows dashboard uploads. |
| 2.3 | Create Terraform module: S3 output bucket | @app/ops-expert | 3 | 2.1 | Bucket created, worker write access configured. |
| 2.4 | Create Terraform module: SQS queue (standard, with DLQ) | @app/ops-expert | 4 | 2.1 | Queue created, DLQ configured, visibility timeout matches expected job duration. |
| 2.5 | Create Terraform module: DynamoDB table (job status/metadata) | @app/ops-expert | 3 | 2.1 | Table with partition key `jobId`, provisioned capacity, TTL for auto-cleanup. |
| 2.6 | Create Terraform module: IAM roles and policies | @app/ops-expert | 5 | 2.2-2.5 | Least-privilege roles for: worker (S3 r/w, SQS r, DynamoDB r/w), dashboard (S3 put, SQS put). |
| 2.7 | Terraform apply + verify all resources in AWS console | @app/ops-expert | 2 | 2.2-2.6 | `terraform apply` succeeds, all resources visible in console. |
| 2.8 | Integration test: write script that submits job message to SQS, polls DynamoDB for status update | @app/ops-expert | 3 | 2.7 | Script runs end-to-end against real AWS resources. |
| 2.9 | Create Terraform destroy workflow + teardown instructions | @app/ops-expert | 3 | 2.7 | `terraform destroy` removes all resources cleanly. Documented in README. |
| 2.10 | Security audit: IAM permissions review | @util/security-reviewer | 4 | 2.6 | No overly permissive roles. Write access scoped to specific buckets. Review report filed. |

---

## Phase 3: Dashboard

| # | Task | Role | Complexity | Deps | Acceptance Criteria |
|---|---|---|---|---|---|
| 3.1 | Scaffold React+Vite+TypeScript project under `dashboard/` | @app/frontend-dev | 3 | — | `npm run dev` starts, empty page renders. |
| 3.2 | [LOCKED] Write component tests for UploadForm | @app/tester | 4 | — | Tests: file selection, drag-drop zone, upload progress indicator. |
| 3.3 | Build UploadForm component (file picker + presigned URL upload) | @app/frontend-dev | 5 | 3.1, 3.2 | User selects video file → uploads to S3 → job created in SQS. |
| 3.4 | [LOCKED] Write component tests for JobStatusList | @app/tester | 4 | — | Tests: polling behavior, status rendering (pending/processing/done/error), timestamps. |
| 3.5 | Build JobStatusList component (polls DynamoDB via API) | @app/frontend-dev | 5 | 3.1, 3.4 | Table of jobs with status, timestamps, worker type. Auto-polls every 5s. |
| 3.6 | [LOCKED] Write component tests for ResultViewer | @app/tester | 5 | — | Tests: JSON table rendering, Canvas frame overlay, empty state. |
| 3.7 | Build ResultViewer component (detection table + Canvas overlay) | @app/frontend-dev | 6 | 3.1, 3.6 | Click job → show detection table + first frame with bbox overlay drawn on Canvas. |
| 3.8 | Build lightweight backend API (Lambda function or simple Express) for dashboard queries | @app/backend-dev | 5 | 2.7 | API endpoints: list jobs, get job detail, get presigned upload URL. |
| 3.9 | Deploy dashboard to S3 static website (Terraform bucket + apply) | @app/ops-expert | 3 | 3.5, 3.7, 3.8 | `terraform apply` creates bucket, `npm run build` + `aws s3 sync` deploys. |
| 3.10 | End-to-end test: upload video → see job in list → view results | @app/tester | 4 | 3.9 | Full cycle works: file upload → SQS → (manual or mock process) → DynamoDB update → visible in dashboard. |

---

## Phase 4: EC2 Worker Deployment

| # | Task | Role | Complexity | Deps | Acceptance Criteria |
|---|---|---|---|---|---|
| 4.1 | Write `poll_and_process.py` — SQS poller loop that calls `process_video()` | @app/backend-dev | 5 | 1.8, 2.7 | Script polls SQS, invokes processor, deletes message on success, logs errors to CloudWatch. |
| 4.2 | Create Terraform module: EC2 t2.micro with user-data script | @app/ops-expert | 5 | 4.1, 2.7 | Instance launches, installs uv + deps, starts poller service (systemd or screen). |
| 4.3 | [LOCKED] Write end-to-end test for EC2 worker path | @app/tester | 6 | 4.2 | Test: submit video via S3 → verify SQS message → wait for DynamoDB status=done → verify results in S3. |
| 4.4 | Launch EC2, verify worker processes jobs | @app/ops-expert | 3 | 4.2, 4.3 | SSH into instance, check logs, upload test video via dashboard, confirm processing. |
| 4.5 | Document EC2 setup: AMI, user-data script, SSH instructions | @app/backend-dev | 3 | 4.4 | README section covers reproduction steps. |

---

## Phase 5: ECS/Fargate + CI/CD v1

| # | Task | Role | Complexity | Deps | Acceptance Criteria |
|---|---|---|---|---|---|
| 5.1 | Write Dockerfile for worker (multi-stage, uv-based, ~200MB) | @app/ops-expert | 4 | 1.8 | `docker build` succeeds, image runs `process_video()` locally. |
| 5.2 | Create Terraform module: ECR repository | @app/ops-expert | 2 | 5.1 | Repository created, push instructions documented. |
| 5.3 | Push worker image to ECR manually (first time) | @app/ops-expert | 3 | 5.2 | Image pushed, `docker pull` from ECR works. |
| 5.4 | Create GitHub Actions workflow: build worker image → push to ECR | @app/ops-expert | 5 | 5.3 | On push to `main` with changes in `worker/`, image builds and pushes. |
| 5.5 | Create Terraform module: ECS cluster + Fargate task definition + service | @app/ops-expert | 6 | 5.1, 2.7 | Fargate task uses same worker image, SQS queue-depth autoscaling configured. |
| 5.6 | [LOCKED] Write integration test for Fargate path | @app/tester | 6 | 5.5 | Test: submit job → verify Fargate task starts → job completes → check results. |
| 5.7 | Deploy Fargate, verify worker processes jobs from queue | @app/ops-expert | 3 | 5.5, 5.6 | Jobs drain from SQS, DynamoDB shows processed status. |
| 5.8 | Compare EC2 vs Fargate: cold start, cost, operational notes | @app/backend-dev | 3 | 4.4, 5.7 | Qualitative comparison notes saved for Phase 7. |

---

## Phase 6: Lambda + CI/CD v2

| # | Task | Role | Complexity | Deps | Acceptance Criteria |
|---|---|---|---|---|---|
| 6.1 | Create Lambda handler wrapper around `process_video()` | @app/backend-dev | 4 | 1.8 | Lambda handler receives SQS event, calls `process_video()`, handles errors. |
| 6.2 | Build + push Lambda container image (minimize size for cold start) | @app/ops-expert | 5 | 6.1 | Image < 3GB (Lambda limit), tested locally with `lambda-runtime` mock. |
| 6.3 | Create Terraform module: Lambda function + SQS event-source mapping | @app/ops-expert | 5 | 6.2, 2.7 | Lambda triggered by SQS, IAM roles correct, DLQ configured. |
| 6.4 | Update CI/CD: add Terraform auto-apply stage after image build | @app/ops-expert | 4 | 5.4, 6.3 | GitHub Actions runs `terraform plan` → `terraform apply` when Lambda changes. |
| 6.5 | [LOCKED] Write integration test for Lambda path | @app/tester | 7 | 6.3 | Test: submit job → Lambda invoked → DynamoDB update → verify results. Include cold-start timing. |
| 6.6 | Deploy Lambda, test cold-start behavior, measure latency | @app/ops-expert | 4 | 6.3, 6.5 | Document cold start time, warm invocation time, any timeouts. |
| 6.7 | Security audit: Lambda IAM roles + SQS trigger permissions | @util/security-reviewer | 4 | 6.3 | Least-privilege verified. Lambda cannot list/delete from S3, only read/write specific paths. |
| 6.8 | Compare EC2 vs Fargate vs Lambda: latency, cost estimates, cold start, operational complexity | @app/backend-dev | 4 | 4.4, 5.7, 6.6 | Structured comparison saved for Phase 7. |

---

## Phase 7: Documentation & Wrap-up

| # | Task | Role | Complexity | Deps | Acceptance Criteria |
|---|---|---|---|---|---|
| 7.1 | Create architecture diagram (Mermaid or draw.io) | @app/technical-writer | 4 | All | Diagram shows: S3→SQS→Worker→S3+DDB flow, with all 3 compute variants. |
| 7.2 | Write cost comparison document (EC2 vs Fargate vs Lambda) | @app/technical-writer | 4 | 6.8 | Structured table: setup complexity, latency, estimated $/1k jobs, cold start, operational burden. |
| 7.3 | Write deployment guide (beginner-oriented, step-by-step) | @app/technical-writer | 5 | 7.1, 0.1-0.4 | Guide lets a beginner deploy the full pipeline from zero. References PREREQUISITES.md. |
| 7.4 | Write README.md — project overview, setup, usage, teardown | @app/technical-writer | 4 | 7.1-7.3 | Covers what, why, how. |
| 7.5 | Write teardown instructions / `terraform destroy` + S3 empty checklist | @app/technical-writer | 2 | 2.9 | Clear steps to avoid lingering free-tier costs. |
| 7.6 | Final status report — what was built, what was learned | @app/technical-writer | 3 | All | Summary of project outcome. |

---

## Complexity Summary

| Phase | Tasks | Avg Complexity | Total Complexity |
|---|---|---|---|
| 0 | 4 | 2.0 | 8 |
| 1 | 9 | 4.2 | 38 |
| 2 | 10 | 3.6 | 36 |
| 3 | 10 | 4.5 | 45 |
| 4 | 5 | 4.4 | 22 |
| 5 | 8 | 4.1 | 33 |
| 6 | 8 | 4.6 | 37 |
| 7 | 6 | 3.7 | 22 |
| **Total** | **60** | **4.0** | **241** |
