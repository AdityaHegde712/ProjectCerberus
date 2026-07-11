# PLAN — Distributed Batch Inference Pipeline

**Project**: AV Co-Pilot infra prep — YOLOv8 video inference pipeline with swappable compute  
**Owner**: Aditya  
**Personal Goal**: Learn AWS compute deployment models (EC2, ECS/Fargate, Lambda)  
**Project Objective**: Production-grade batch inference pipeline  
**Budget**: AWS Free Tier only. Tear down between sessions.  
**Region**: `us-east-1`  
**Monorepo**: ProjectCerberus (single repo: worker/ + dashboard/ + terraform/ + docs/)

---

## In Scope

- Video upload via web dashboard → S3 → SQS queue
- Worker processes video: YOLOv8 object detection per frame
- Results stored as JSON in S3, job metadata in DynamoDB
- Worker compute: EC2 → ECS/Fargate → Lambda (same function, 3 invokers)
- Dashboard: upload form, job status list, result viewer (table + frame overlay)
- IaC: Terraform (local state → S3+DDB backend)
- CI/CD: GitHub Actions (iterative: image → +frontend → +TF)
- Observability: CloudWatch logs + queue-depth alarm
- Documentation: architecture diagram, deployment guide, cost comparison writeup

## Explicitly Out of Scope

- User authentication / multi-tenant — no auth, single-user
- Fine-tuned YOLO model — off-the-shelf weights only
- Real-time / streaming inference — batch only
- GPU acceleration — CPU inference (free tier compatible)
- Video output rendering — JSON-only output, no annotated video
- Mobile app — web dashboard only
- Multi-region deployment — single region

---

## Architecture Overview

```
User ──→ Dashboard (S3 static site)
              │
              ├── Upload video → S3 (input bucket)
              ├── Write job → SQS queue
              └── Poll job status → DynamoDB
                          
SQS ──→ Worker (process_video() function)
              │
              ├── Read video from S3
              ├── Run YOLOv8 detection
              ├── Write results JSON → S3 (output bucket)
              └── Update job status → DynamoDB

3 compute invokers (same function):
  1. EC2: poll_sqs.py daemon, manual SSH
  2. Fargate: ECS task with queue-depth autoscaling
  3. Lambda: container-image function, SQS trigger
```

---

## Version Roadmap

The project is organized as 3 versions, each delivering a complete working system with a different compute backend.

| Version | Phases | Compute | CI/CD | Learning Focus |
|---|---|---|---|---|
| **v1.0** | 1 → 2 → 3 → 4 | EC2 t2.micro | None (manual deploy) | Raw AWS compute, SSH, IAM, systemd, polling loop |
| **v2.0** | → 5 | Fargate + ECS | v1: image build + v2: frontend deploy | Containerization, ECR, ECS, autoscaling |
| **v3.0** | → 6 | Lambda (container-image) | v3: +Terraform auto-apply | Serverless constraints, cold start, SQS triggers |

Shared across all versions: core worker logic (Phase 1), AWS infra (Phase 2), dashboard (Phase 3). Only the compute invoker changes.

---

## Phases

### ✅ Phase 0 — Environment Setup [Completed by Owner]
- Terraform installed, AWS CLI configured, git repo initialized + pushed to GitHub
- All tools verified

---

### v1.0 — EC2 Worker

### Phase 1 — Core Worker Logic + TDD [v1.0 | Role: @app/tester + @ml/model-scientist]

- **TDD Locked**: All unit tests written first (see tester workflow: write → confirm fail → signal → wait → re-run)
- Define `JobInput` / `JobResult` / `Detection` data schemas (Pydantic)
- YOLO bbox format: `[x_center, y_center, width, height]` normalized 0-1 (standard YOLO)
- Implement `process_video()` — reads video from S3 via storage adapter, runs YOLOv8, writes JSON results
- Implement YOLO wrapper abstraction (model swappable without touching pipeline logic)
- Implement S3 storage adapter (read/write abstraction, local file mock for testing)
- All tests pass locally without AWS (mocked S3, mock video frames)

### Phase 2 — AWS Infrastructure [v1.0 | Role: @app/ops-expert + @app/tester + @util/security-reviewer]

- Terraform modules: S3 (input + output buckets), SQS queue + DLQ, DynamoDB table, IAM roles
- Local state management (migrate to S3+DDB in v3.0)
- IAM roles created via Terraform CLI — no console work needed
- `terraform apply` creates all resources
- Integration test: script submits test message to SQS, verifies DynamoDB write
- Destroy workflow: `terraform destroy` removes all resources (run after each session to avoid free-tier costs)

### Phase 3 — Dashboard + API Lambda [v1.0 | Role: @app/frontend-dev + @app/backend-dev]

- React + Vite + TypeScript app under `dashboard/`
- Upload form: drag-drop or file picker → presigned S3 upload → push job to SQS
- Job status page: polls DynamoDB via API Lambda (Lambda + API Gateway, NOT direct SDK call)
- Result viewer: table of detections (class, confidence, bbox) + single frame rendered on Canvas with manually-drawn bounding boxes (Canvas is a blank API — requires JavaScript drawing logic)
- Deploy to S3 as static website
- **Initial docs** (after architecture finalized): architecture diagram (Mermaid + Excalidraw)

### Phase 4 — EC2 Worker Deployment [v1.0 | Role: @app/backend-dev + @app/ops-expert]

- `poll_and_process.py` — long-running script on EC2: polls SQS (long polling), calls `process_video()`, deletes message on success
- Launch EC2 t2.micro via Terraform (user-data script installs uv, clones repo, starts poller)
- Security group: SSH from owner IP only, outbound internet
- Manual SSH verification + log inspection
- **Initial docs**: deployment guide (EC2 focused, CLI snippets only, no screenshots), README.md basics
- End-to-end test: upload video via dashboard → job processed on EC2 → results visible

> **v1.0 is complete here.** Running system with EC2 compute, dashboard, API, and infra. Move to v2.0 for Fargate swap.

---

### v2.0 — Fargate + CI/CD

### Phase 5 — Swap EC2 → Fargate + CI/CD [v2.0 | Role: @app/ops-expert + @app/backend-dev]

**Compute swap**:
- Containerize worker: `Dockerfile.fargate` (multi-stage, uv-based, no Lambda runtime client)
- Push image to ECR (manual first time, automated via CI/CD thereafter)
- Terraform: ECS cluster, Fargate task definition, service with SQS queue-depth autoscaling

**CI/CD v1 — Worker image build**:
- GitHub Actions workflow: on push to `main` with changes in `worker/` → build image → push to ECR → update Fargate service

**CI/CD v2 — Frontend deploy**:
- GitHub Actions workflow: on push to `main` with changes in `dashboard/` → `npm run build` → `aws s3 sync` to S3 static website bucket

**Observation & research**:
- @app/backend-dev: compare cold start, cost-per-job vs EC2 (qualitative notes)
- **@util/research-analyst**: begin cost comparison research across compute models (pricing data, cold-start benchmarks)

> **v2.0 is complete here.** Fargate running, CI/CD automated, frontend deploying. Move to v3.0 for Lambda swap.

---

### v3.0 — Lambda + CI/CD v3

### Phase 6 — Swap Fargate → Lambda + CI/CD v3 [v3.0 | Role: @app/ops-expert + @app/backend-dev]

**Compute swap**:
- Create Lambda handler wrapper: `lambda_handler(event, context)` parses SQS event, calls `process_video()`, handles batch partial failures
- Container-image Lambda: `Dockerfile.lambda` (includes Lambda runtime interface client, minimized for cold start)
- Terraform: Lambda function + SQS event-source mapping + IAM roles
- Cold start optimization: reserved concurrency, image size management

**CI/CD v3 — +Terraform auto-apply**:
- GitHub Actions: after image build → `terraform plan` → auto-apply on `main` branch
- Migrate Terraform state from local to S3+DynamoDB backend (required for CI/CD)

**Final comparison data**:
- @app/backend-dev: collect latency, cold start, cost for Lambda vs EC2 vs Fargate
- @util/research-analyst: finalize cost comparison research

---

### Final Wrap-Up

### Phase 7 — Documentation Finalization [Role: @app/technical-writer + @util/codebase-doc]

- **@util/codebase-doc**: Generate `CODEBASE.md` (full codebase documentation)
- **@app/technical-writer**:
  - Update/correct architecture diagram if architecture changed during development
  - Update deployment guide with Fargate + Lambda sections
  - Finalize cost comparison document (incorporate @util/research-analyst data + @app/backend-dev observations)
  - Update README.md with final CI/CD status badges, cost comparison link
  - Teardown checklist (S3 empty → terraform destroy → CloudWatch cleanup → verify billing)
  - Final status report: what was built, key learnings, what could be improved

---

## Agent Assignments by Phase

| Phase | Version | Primary Agent(s) | Supporting Agent(s) |
|---|---|---|---|
| 0 | — | _Manual (Owner — completed)_ | — |
| 1 | v1.0 | @app/tester, @ml/model-scientist | @ml/data-engineer |
| 2 | v1.0 | @app/ops-expert | @app/tester, @util/security-reviewer |
| 3 | v1.0 | @app/frontend-dev, @app/backend-dev | @app/tester, @app/technical-writer (docs) |
| 4 | v1.0 | @app/backend-dev, @app/ops-expert | @app/tester, @app/technical-writer (docs) |
| 5 | v2.0 | @app/ops-expert, @app/backend-dev | @app/tester, @util/research-analyst |
| 6 | v3.0 | @app/ops-expert, @app/backend-dev | @app/tester, @util/security-reviewer, @util/research-analyst |
| 7 | — | @app/technical-writer, @util/codebase-doc | — |

---

## Dependencies & Sequencing

```
Phase 0 ✅ ──→ Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 4
                                                       │
                                                  [v1.0 done]
                                                       │
                                                  Phase 5 (Fargate + CI/CD)
                                                       │
                                                  [v2.0 done]
                                                       │
                                                  Phase 6 (Lambda + CI/CD)
                                                       │
                                                  [v3.0 done]
                                                       │
                                                  Phase 7 (Final docs)
```

- Phases 1-3: core shared across all versions
- Phase 4 = v1.0 milestone (running EC2 system)
- Phase 5 = v2.0 milestone (Fargate + CI/CD running)
- Phase 6 = v3.0 milestone (Lambda running, full CI/CD)
- Phase 7 = final wrap-up (no new features)

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Worker interface | Single `process_video()` function | Enables clean compute swap — each target is just an invoker |
| Compute order | EC2 → Fargate → Lambda | Pedagogical progression: raw compute → containerized → serverless |
| Version structure | v1.0/v2.0/v3.0 within single plan | Core shared, compute swapped. Clearer than separate plans. |
| Backend API | Lambda + API Gateway (Phase 3) | Separate from worker Lambda (Phase 6). Simple, serverless, teaches Lambda early. |
| Data format | JSON only (no annotated video) | Lightweight, analysis-friendly, avoids FFmpeg dependency |
| TDD | Red-Green-Refactor for core logic | Tests as executable spec; prevents regression across compute swaps |
| Python toolchain | uv | Fast, modern, clean Docker builds |
| Terraform state | Local → S3+DDB (migrate v3.0) | Learn both patterns; migrate when CI/CD auto-apply lands |
| CI/CD | Iterative (image → +frontend → +TF) | Grows with project complexity across versions |
| Dashboard hosting | S3 static website | Simple, cheap, real deployment. CloudFront optional later |
| YOLO bbox format | [x_center, y_center, width, height] normalized 0-1 | Standard YOLO output format (not COCO) |
| Doc timeline | Initial docs early (Phase 3-4), final docs Phase 7 | Docs usable while building, not just at end |
| Cost research | @util/research-analyst + @app/backend-dev notes | Research done during v2.0/v3.0, finalized Phase 7 |

---

## Plan Version

- **Version**: 1.1 (restructured: versions + order + doc timeline + CI/CD progression)
- **Status**: Awaiting Owner confirmation
- **Date**: 2026-07-08
