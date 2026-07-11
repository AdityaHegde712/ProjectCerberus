# PLAN — @app/backend-dev

**Role**: Backend API, SQS poller, Lambda handler, integration glue.

## Tasks

### 3.8 — Build backend API for dashboard queries (Lambda + API Gateway)

- Implementation: **Lambda function behind API Gateway HTTP API** (single choice, no alternatives)
- API endpoints:
  - `POST /upload` — generate presigned S3 URL + create SQS job message
  - `GET /jobs` — list recent jobs from DynamoDB
  - `GET /jobs/:id` — single job detail + result S3 key
- Terraform module: `terraform/modules/api-lambda/` (Lambda function + API Gateway + IAM role)
- Separate from the worker Lambda (Phase 6) — different function, different trigger, same infrastructure pattern

### 4.1 — Write `poll_and_process.py` (EC2 SQS poller)

- Long-running loop:
  1. Poll SQS (long polling, WaitTimeSeconds=20)
  2. For each message: call `process_video()` from processor module
  3. On success: delete message from SQS
  4. On failure: log error to CloudWatch, message goes to DLQ after max retries
- Handle graceful shutdown (SIGTERM/SIGINT)
- Must work with the EC2 user-data systemd service (task 4.2)

### 4.5 — Document EC2 setup

- Step-by-step: AMI details, packages, start poller, verify logs
- How to SSH in and check status

### 6.1 — Create Lambda handler wrapper

- `lambda_handler(event, context)`:
  - Parse SQS event (batch of records)
  - For each record: call `process_video()`
  - Handle errors per-message (don't fail the whole batch)
  - Return batch partial failures for SQS retry
- Reuse same `worker/src/` modules — no duplicate code

### 5.8, 6.8 — Cost/comparison notes

- During each compute swap, collect qualitative notes:
  - Setup effort (minutes)
  - Cold start time (seconds)
  - Job latency (seconds per 100 frames)
  - Operational complexity (1-10 scale)
  - Estimated cost per 1000 jobs
- Save structured notes in `docs/comparison-notes/` for Phase 7 writer

## Output Files

```
worker/src/
  poll_and_process.py  -- EC2 SQS poller daemon
  lambda_handler.py    -- Lambda worker entry point (Phase 6)

backend/api-lambda/
  handler.py            -- API Lambda handler (Phase 3 — dashboard backend)

terraform/modules/
  api-lambda/           -- API Lambda TF module (Phase 3)

docs/comparison-notes/
  ec2-notes.md
  fargate-notes.md
  lambda-notes.md
```
