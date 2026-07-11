# TASKS — Distributed Batch Inference Pipeline

**Complexity scale**: 1 (trivial) → 10 (extremely complex)  
**Status**: pending | in_progress | completed | blocked | cancelled  
**Locked**: Tasks marked "[LOCKED]" cannot be modified by implementation agents (test contracts).

---

## Phase 0: Environment Setup [COMPLETED]

| # | Task | Complexity | Deps | Status |
|---|---|---|---|---|
| 0.1 | Install Terraform | 2 | — | ✅ completed |
| 0.2 | Configure AWS CLI (IAM user + access keys) | 3 | — | ✅ completed |
| 0.3 | Initialize git repo + push to GitHub | 2 | — | ✅ completed |
| 0.4 | Run verification checklist | 1 | 0.1, 0.2, 0.3 | ✅ completed |

---

## v1.0 — EC2 Worker

### Phase 1: Core Worker Logic + TDD

| # | Task | Role | Complexity | Deps | Acceptance Criteria |
|---|---|---|---|---|---|
| 1.1 | [LOCKED] Write unit tests for JobInput/JobResult/Detection schemas (Pydantic) | @app/tester | 4 | — | Tests validate field types, defaults, and serialization. Red step passes (tests fail before impl). |
| 1.2 | Implement data schema models in `worker/src/schemas.py` | @ml/data-engineer | 3 | 1.1 | Pydantic models pass all tests from 1.1. |
| 1.3 | [LOCKED] Write unit tests for YOLO wrapper abstraction | @app/tester | 5 | 1.2 | Tests verify mock model interface: `load_model()`, `predict(frame) -> List[Detection]`. Red step passes. |
| 1.4 | Implement YOLO wrapper in `worker/src/detector.py` | @ml/model-scientist | 4 | 1.3 | Wrapper loads ultralytics YOLOv8n, returns typed Detections (YOLO format: x_center, y_center, width, height normalized). Tests pass. |
| 1.5 | [LOCKED] Write unit tests for S3 storage adapter (with local file mock) | @app/tester | 5 | 1.2 | Tests verify read/write with local filesystem mock. Red step passes. |
| 1.6 | Implement S3 storage adapter in `worker/src/storage.py` | @ml/data-engineer | 4 | 1.5 | Adapter handles local file fallback (no AWS) + S3 client. Tests pass. |
| 1.7 | [LOCKED] Write unit tests for `process_video()` function | @app/tester | 6 | 1.4, 1.6 | Tests verify: mock video → mock YOLO output → correct JobResult JSON. Edge cases: empty video, corrupt frames, no detections. Red step passes. |
| 1.8 | Implement `process_video()` in `worker/src/processor.py` | @ml/model-scientist | 5 | 1.7 | Function orchestrates: read frames → detect → write results. All tests pass. |
| 1.9 | Run full Phase 1 test suite + code coverage report | @app/tester | 2 | 1.2, 1.4, 1.6, 1.8 | All tests green, coverage > 80% on core modules. |

### Phase 2: AWS Infrastructure

| # | Task | Role | Complexity | Deps | Acceptance Criteria |
|---|---|---|---|---|---|
| 2.1 | [LOCKED] Write shell-based tests for Terraform module outputs | @app/tester | 4 | — | Tests verify expected resource names, IAM policies, bucket configurations. |
| 2.2 | Create Terraform module: S3 input bucket with CORS policy | @app/ops-expert | 4 | 2.1 | Bucket created, CORS allows dashboard uploads. |
| 2.3 | Create Terraform module: S3 output bucket | @app/ops-expert | 3 | 2.1 | Bucket created, worker write access configured. |
| 2.4 | Create Terraform module: SQS queue (standard, with DLQ) | @app/ops-expert | 4 | 2.1 | Queue created, DLQ configured, visibility timeout matches expected job duration. |
| 2.5 | Create Terraform module: DynamoDB table (job status/metadata) | @app/ops-expert | 3 | 2.1 | Table with partition key `jobId`, provisioned capacity, TTL for auto-cleanup. |
| 2.6 | Create Terraform module: IAM roles and policies (least-privilege) | @app/ops-expert | 5 | 2.2-2.5 | Roles: worker (S3 r/w, SQS r, DynamoDB r/w), dashboard (S3 put, SQS put). Created via Terraform CLI — no console needed. |
| 2.7 | Terraform apply + verify all resources in AWS console | @app/ops-expert | 2 | 2.2-2.6 | `terraform apply` succeeds, all resources visible in console. |
| 2.8 | Integration test: script submits job message to SQS, polls DynamoDB | @app/ops-expert | 3 | 2.7 | Script runs end-to-end against real AWS resources. |
| 2.9 | Create Terraform destroy workflow + teardown instructions | @app/ops-expert | 3 | 2.7 | `terraform destroy` removes all resources cleanly. Documented. |
| 2.10 | Security audit: IAM permissions review | @util/security-reviewer | 4 | 2.6 | No overly permissive roles. Write access scoped to specific buckets. Review report filed. |

### Phase 3: Dashboard + API Lambda

| # | Task | Role | Complexity | Deps | Acceptance Criteria |
|---|---|---|---|---|---|
| 3.1 | Scaffold React+Vite+TypeScript project under `dashboard/` | @app/frontend-dev | 3 | — | `npm run dev` starts, empty page renders. |
| 3.2 | [LOCKED] Write component tests for UploadForm | @app/tester | 4 | — | Tests: file selection, drag-drop zone, upload progress indicator. |
| 3.3 | Build UploadForm component (file picker + presigned URL upload) | @app/frontend-dev | 5 | 3.1, 3.2 | User selects video file → uploads to S3 → job created in SQS. |
| 3.4 | [LOCKED] Write component tests for JobStatusList | @app/tester | 4 | — | Tests: polling behavior, status rendering (pending/processing/done/error), timestamps. |
| 3.5 | Build JobStatusList component (polls DynamoDB via API Lambda) | @app/frontend-dev | 5 | 3.1, 3.4 | Table of jobs with status, timestamps, worker type. Auto-polls every 5s. |
| 3.6 | [LOCKED] Write component tests for ResultViewer | @app/tester | 5 | — | Tests: JSON table rendering, Canvas frame overlay with manually-drawn bbox, empty state. |
| 3.7 | Build ResultViewer component (detection table + Canvas overlay) | @app/frontend-dev | 6 | 3.1, 3.6 | Click job → show detection table + first frame with bbox drawn on Canvas (manual JS drawing — Canvas is blank API, no auto-render). |
| 3.8 | Build backend API (Lambda + API Gateway) for dashboard queries | @app/backend-dev | 5 | 2.7 | Lambda function with endpoints: list jobs, get job detail, presigned upload URL. Terraform module in `modules/api-lambda/`. |
| 3.9 | Deploy dashboard to S3 static website (Terraform bucket + apply) | @app/ops-expert | 3 | 3.5, 3.7, 3.8 | `terraform apply` creates bucket, `npm run build` + `aws s3 sync` deploys. |
| 3.10 | Create initial architecture diagram (Mermaid + Excalidraw) | @app/technical-writer | 4 | All Phase 3 | Diagram shows S3→SQS→Worker→S3+DDB flow. 3 compute variants as callouts. |
| 3.11 | End-to-end test: upload video → see job in list → view results | @app/tester | 4 | 3.9, 3.10 | Full cycle works: file upload → SQS → (manual or mock process) → DynamoDB update → visible in dashboard. |

### Phase 4: EC2 Worker Deployment

| # | Task | Role | Complexity | Deps | Acceptance Criteria |
|---|---|---|---|---|---|
| 4.1 | Write `poll_and_process.py` — SQS poller loop that calls `process_video()` | @app/backend-dev | 5 | 1.8, 2.7 | Script polls SQS (long polling), invokes processor, deletes message on success, logs errors to CloudWatch. |
| 4.2 | Create Terraform module: EC2 t2.micro with security group + user-data script | @app/ops-expert | 5 | 4.1, 2.7 | Instance launches, installs uv + deps, starts poller (systemd). SSH from owner IP only. |
| 4.3 | [LOCKED] Write end-to-end test for EC2 worker path | @app/tester | 6 | 4.2 | Test: submit video via S3 → verify SQS message → wait for DynamoDB status=done → verify results in S3. |
| 4.4 | Launch EC2, verify worker processes jobs | @app/ops-expert | 3 | 4.2, 4.3 | SSH into instance, check logs, upload test video via dashboard, confirm processing. |
| 4.5 | Write deployment guide (EC2 focused, CLI snippets only) | @app/technical-writer | 4 | 4.4 | Step-by-step from PREREQUISITES through EC2 deploy. No screenshots (agents can't take them). |
| 4.6 | Write README.md — project overview, setup, usage, teardown | @app/technical-writer | 3 | 4.5 | Covers what, why, how. References architecture diagram and deployment guide. |
| 4.7 | Document EC2 setup: AMI, user-data script, SSH instructions | @app/backend-dev | 3 | 4.4 | README section covers reproduction steps. |

> **v1.0 complete.** Running system with EC2 compute, dashboard, API, infra.

---

## v2.0 — Fargate + CI/CD

### Phase 5: Swap EC2 → Fargate + CI/CD

| # | Task | Role | Complexity | Deps | Acceptance Criteria |
|---|---|---|---|---|---|
| 5.1 | Write Dockerfile for Fargate worker (multi-stage, uv-based, no Lambda runtime) | @app/ops-expert | 4 | 1.8 | `docker build` succeeds, image runs `process_video()` locally. |
| 5.2 | Create Terraform module: ECR repository | @app/ops-expert | 2 | 5.1 | Repository created, push instructions documented. |
| 5.3 | Push worker image to ECR manually (first time) | @app/ops-expert | 3 | 5.2 | Image pushed, `docker pull` from ECR works. |
| 5.4 | Create GitHub Actions workflow CI/CD v1: build Fargate image → push to ECR | @app/ops-expert | 5 | 5.3 | On push to `main` with changes in `worker/`, image builds and pushes to ECR. |
| 5.5 | Create Terraform module: ECS cluster + Fargate task definition + service | @app/ops-expert | 6 | 5.1, 2.7 | Fargate task uses worker image, SQS queue-depth autoscaling configured. |
| 5.6 | Create GitHub Actions workflow CI/CD v2: build + deploy frontend to S3 | @app/ops-expert | 4 | 5.4, 3.9 | On push to `main` with changes in `dashboard/`, `npm run build` + `aws s3 sync` to static site. |
| 5.7 | [LOCKED] Write integration test for Fargate path | @app/tester | 6 | 5.5 | Test: submit job → verify Fargate task starts → job completes → check results. |
| 5.8 | Deploy Fargate, verify worker processes jobs from queue | @app/ops-expert | 3 | 5.5, 5.7 | Jobs drain from SQS, DynamoDB shows processed status. |
| 5.9 | Compare EC2 vs Fargate: cold start, cost, operational notes | @app/backend-dev | 3 | 4.4, 5.8 | Qualitative comparison notes saved to `docs/comparison-notes/`. |
| 5.10 | Begin cost comparison research across compute models | @util/research-analyst | 5 | — | Research pricing data, cold-start benchmarks, best practices. Output: structured notes for cost-comparison.md. |

> **v2.0 complete.** Fargate running, CI/CD automated (worker image + frontend deploy).

---

## v3.0 — Lambda + CI/CD

### Phase 6: Swap Fargate → Lambda + CI/CD v3

| # | Task | Role | Complexity | Deps | Acceptance Criteria |
|---|---|---|---|---|---|
| 6.1 | Create Lambda handler wrapper around `process_video()` | @app/backend-dev | 4 | 1.8 | Lambda handler receives SQS event, calls `process_video()`, handles batch partial failures. |
| 6.2 | Write Dockerfile for Lambda worker (includes lambda-runtime-interface-client, minimized for cold start) | @app/ops-expert | 5 | 6.1 | Image < 3GB (Lambda limit), tested locally with lambda-runtime mock. |
| 6.3 | Create Terraform module: Lambda function + SQS event-source mapping + IAM | @app/ops-expert | 5 | 6.2, 2.7 | Lambda triggered by SQS, IAM roles least-privilege, DLQ configured. |
| 6.4 | Migrate Terraform state from local to S3+DynamoDB backend | @app/ops-expert | 4 | 2.7 | State migration script executed. Future `terraform apply` uses remote state. |
| 6.5 | Update CI/CD to v3: add Terraform auto-apply stage after image build | @app/ops-expert | 4 | 5.4, 6.4 | GitHub Actions runs `terraform plan` → auto-apply on `main`. |
| 6.6 | [LOCKED] Write integration test for Lambda path | @app/tester | 7 | 6.3 | Test: submit job → Lambda invoked → DynamoDB update → verify results. Include cold-start timing. |
| 6.7 | Deploy Lambda, test cold-start behavior, measure latency | @app/ops-expert | 4 | 6.3, 6.6 | Document cold start time, warm invocation time, any timeouts. |
| 6.8 | Security audit: Lambda IAM roles + SQS trigger permissions | @util/security-reviewer | 4 | 6.3 | Least-privilege verified. Lambda cannot list/delete from S3, only read/write specific paths. |
| 6.9 | Compare EC2 vs Fargate vs Lambda: latency, cost, cold start, operational complexity | @app/backend-dev | 4 | 4.4, 5.8, 6.7 | Structured comparison saved to `docs/comparison-notes/`. |
| 6.10 | Finalize cost comparison research for all 3 compute models | @util/research-analyst | 4 | 5.10 | Complete pricing data, cold-start benchmarks, cost-per-1k-jobs estimates. |

> **v3.0 complete.** Lambda running, full CI/CD with Terraform auto-apply.

---

## Final Wrap-Up

### Phase 7: Documentation Finalization

| # | Task | Role | Complexity | Deps | Acceptance Criteria |
|---|---|---|---|---|---|
| 7.1 | Generate CODEBASE.md (full codebase documentation) | @util/codebase-doc | 4 | All | Comprehensive CODEBASE.md at repo root covering all modules. |
| 7.2 | Update/correct architecture diagram if architecture changed during dev | @app/technical-writer | 3 | 7.1 | Diagram updated to match final architecture. |
| 7.3 | Update deployment guide with Fargate + Lambda sections | @app/technical-writer | 4 | 4.5, 5.8, 6.7 | All 3 compute paths documented. |
| 7.4 | Write cost comparison document (EC2 vs Fargate vs Lambda) | @app/technical-writer | 4 | 6.9, 6.10 | Final formatted document incorporating research + backend notes. |
| 7.5 | Update README.md with final CI/CD badges, cost comparison link | @app/technical-writer | 2 | 7.2-7.4 | README reflects final project state. |
| 7.6 | Write teardown instructions + S3 empty + billing verification checklist | @app/technical-writer | 2 | 2.9 | Clear steps to avoid lingering free-tier costs. |
| 7.7 | Final status report — what was built, key learnings, improvements | @app/technical-writer | 3 | All | Summary of project outcome across all 3 versions. |

---

## Complexity Summary

| Phase | Version | Tasks | Avg Complexity | Total Complexity |
|---|---|---|---|---|
| 0 | — | 4 | 2.0 | 8 ✅ |
| 1 | v1.0 | 9 | 4.2 | 38 |
| 2 | v1.0 | 10 | 3.6 | 36 |
| 3 | v1.0 | 11 | 4.3 | 47 |
| 4 | v1.0 | 7 | 4.1 | 29 |
| 5 | v2.0 | 10 | 4.2 | 42 |
| 6 | v3.0 | 10 | 4.5 | 45 |
| 7 | — | 7 | 3.1 | 22 |
| **Total** | **3 versions** | **68** | **3.9** | **267** |
