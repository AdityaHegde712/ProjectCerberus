# PLAN — Distributed Batch Inference Pipeline

**Project**: AV Co-Pilot infra prep — YOLOv8 video inference pipeline with swappable compute (EC2 → Fargate → Lambda)  
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
- CI/CD: GitHub Actions (iterative: image → +TF → +frontend)
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

## Phases

### Phase 0 — Environment Setup [Owner: Manual via PREREQUISITES.md]
- Install Terraform
- Configure AWS CLI (IAM user + access keys)
- Initialize git repo + push to GitHub
- Verify all tools

### Phase 1 — Core Worker Logic + TDD [Role: @app/tester + @ml/model-scientist]
- **TDD Locked**: Tests written first, before implementation code
- Define `JobInput` / `JobResult` / `Detection` data schemas (Pydantic)
- Implement `process_video()` — reads video from S3 via AWS SDK mock (local file fallback), runs YOLOv8, writes JSON results
- Implement YOLO wrapper abstraction (so model can be swapped without touching pipeline logic)
- Implement S3 storage adapter (read/write abstraction, local file mock)
- All tests pass locally without AWS (mocked S3, mock video frames)

### Phase 2 — AWS Infrastructure v1 [Role: @app/ops-expert + @app/tester]
- Terraform modules: S3 (input + output buckets), SQS queue, DynamoDB table, IAM roles
- Local state management
- `terraform apply` creates all resources
- Integration test: script submits test message to SQS, verifies DynamoDB write
- Separate destroy workflow for teardown between sessions

### Phase 3 — Dashboard [Role: @app/frontend-dev + @app/backend-dev]
- React + Vite + TypeScript app under `dashboard/`
- Upload form: drag-drop or file picker → presigned S3 upload → push job to SQS
- Job status page: polls DynamoDB via API (Lambda API or direct SDK call) — show status, timestamps
- Result viewer: table of detections (class, confidence, bbox) + single frame rendered on Canvas with bounding boxes
- Deploy to S3 as static website

### Phase 4 — EC2 Worker Deployment [Role: @app/backend-dev + @app/ops-expert]
- `poll_and_process.py` — long-running script on EC2: polls SQS, calls `process_video()`, deletes message on success
- Launch EC2 t2.micro via Terraform (user-data script installs deps, starts poller)
- Manual SSH verification
- End-to-end test: upload video via dashboard → job processed on EC2 → results visible
- Create AMI or document the setup commands for reproducibility

### Phase 5 — ECS/Fargate + CI/CD v1 [Role: @app/ops-expert + @app/backend-dev]
- Containerize worker (Dockerfile with uv, multi-stage for small image)
- Push image to ECR via GitHub Actions (worker build pipeline)
- Terraform: ECS cluster, Fargate task definition, service with SQS queue-depth autoscaling
- CI/CD: GitHub Actions build → push to ECR → update Fargate service
- Compare: cold start, cost-per-job vs EC2 (qualitative)

### Phase 6 — Lambda + CI/CD v2 [Role: @app/ops-expert + @app/backend-dev]
- Container-image Lambda function (same worker code, Lambda handler wrapper)
- Terraform: Lambda function + event-source mapping (SQS trigger)
- CI/CD update: +Terraform auto-apply stage
- Cold start optimization: Lambda reserved concurrency, image size management
- Compare: latency, cost, cold start vs Fargate vs EC2 (qualitative + data)

### Phase 7 — Documentation & Wrap-up [Role: @app/technical-writer]
- Architecture diagram (draw.io or Mermaid)
- Cost comparison writeup across 3 compute models
- Deployment guide (beginner-friendly, references PREREQUISITES.md)
- README.md with project overview, setup, usage
- Teardown scripts / instructions
- Final status document

---

## Agent Assignments by Phase

| Phase | Primary Agent(s) | Supporting Agent(s) |
|---|---|---|
| 0 | _Manual (Owner)_ | — |
| 1 | @app/tester, @ml/model-scientist | @ml/data-engineer |
| 2 | @app/ops-expert | @app/tester, @util/security-reviewer |
| 3 | @app/frontend-dev, @app/backend-dev | @app/tester |
| 4 | @app/backend-dev, @app/ops-expert | @app/tester |
| 5 | @app/ops-expert, @app/backend-dev | @app/tester |
| 6 | @app/ops-expert, @app/backend-dev | @app/tester, @util/security-reviewer |
| 7 | @app/technical-writer | — |

---

## Dependencies & Sequencing

```
Phase 0 ──→ Phase 1 ──→ Phase 2 ──→ Phase 3
                                       │
                ┌──────────────────────┘
                ▼
           Phase 4 (EC2)
                │
           Phase 5 (Fargate + CI/CD)
                │
           Phase 6 (Lambda + CI/CD)
                │
           Phase 7 (Docs)
```

- Phase 3 (Dashboard) can start after Phase 2 (infra exists) — or partially mock with local data
- Phase 4/5/6 are sequential: each swap builds on the previous
- Phase 7 is last but cost comparison notes should be gathered during Phases 4-6

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Worker interface | Single `process_video()` function | Enables clean compute swap — each target is just an invoker |
| Data format | JSON only (no annotated video) | Lightweight, analysis-friendly, avoids FFmpeg dependency |
| TDD | Red-Green-Refactor for core logic | Tests as executable spec; prevents regression across compute swaps |
| Python toolchain | uv | Fast, modern, clean Docker builds |
| Terraform state | Local → S3+DDB | Learn both patterns; migrate when CI/CD lands |
| CI/CD | Iterative (image → +TF → +frontend) | Grows with project complexity |
| Dashboard hosting | S3 static website | Simple, cheap, real deployment. CloudFront optional later |

---

## Open Questions (Resolved)

All architectural questions have been resolved with the Owner during the /grill-me session. See STATUS.md for the full decision log.

---

## Plan Version

- **Version**: 1.0
- **Status**: Awaiting Owner confirmation
- **Date**: 2026-07-08
