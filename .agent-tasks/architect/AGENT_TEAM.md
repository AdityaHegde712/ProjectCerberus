# AGENT TEAM — Distributed Batch Inference Pipeline

## Static Agents (Pre-existing Roster)

| Agent | Role | Phases | Key Responsibilities |
|---|---|---|---|
| @app/tester | Test specialist | 1-6 | Writes [LOCKED] unit/integration tests before implementation. Red-Green-Refactor enforcement. |
| @ml/model-scientist | ML model implementation | 1 | YOLOv8 wrapper, `process_video()` inference logic, model loading abstraction. |
| @ml/data-engineer | Data/ETL pipeline | 1-2 | S3 storage adapter, job schema (Pydantic), data I/O abstractions. |
| @app/backend-dev | Backend/API | 3-6 | Backend API for dashboard, SQS poller (EC2), Lambda handler, EC2 setup docs. |
| @app/frontend-dev | Dashboard UI | 3 | React+Vite+TS: UploadForm, JobStatusList, ResultViewer with Canvas overlay. |
| @app/ops-expert | Infrastructure | 2, 4-6 | Terraform modules for all AWS resources, CI/CD workflows, Docker containerization, EC2/ECS/Lambda deployment. |
| @app/technical-writer | Documentation | 7 | Architecture diagram, deployment guide, cost comparison, README, teardown docs. |
| @util/security-reviewer | Security audit | 2, 6 | IAM permissions review, least-privilege validation, audit reports. |

## Dynamic Agents (None Required)

All tasks mapped cleanly to existing static agents. No `@dynamic-TBD` gaps identified. The static roster is sufficient for every phase.

## Agent Permissions & Boundaries

| Agent | Can Write To | Cannot Modify | Notes |
|---|---|---|---|
| @app/tester | `tests/` | Any `src/` file, any `terraform/` file | TDD contract — tests are immutable spec |
| @ml/model-scientist | `worker/src/` | `tests/`, `dashboard/`, `terraform/` | Implementation only |
| @ml/data-engineer | `worker/src/` | `tests/`, `dashboard/`, `terraform/` | Implementation only |
| @app/backend-dev | `worker/src/`, `backend/` | `tests/`, `dashboard/src/`, `terraform/` | Backend + API code |
| @app/frontend-dev | `dashboard/src/` | `tests/`, `worker/`, `terraform/` | Frontend only |
| @app/ops-expert | `terraform/`, `worker/Dockerfile`, `.github/workflows/` | `tests/`, `worker/src/` (except Dockerfile), `dashboard/src/` | Infra + CI/CD |
| @app/technical-writer | `docs/`, `README.md` | All source code | Documentation only |
| @util/security-reviewer | (Read-only + report file) | No write to source | Audit reports only |

## Communication Pattern

- **@app/tester** writes tests and signals completion. Implementation agents then code to satisfy tests.
- **@app/ops-expert** creates AWS resources. **@app/backend-dev** and **@app/frontend-dev** consume them (bucket names, queue URLs passed via Terraform outputs / config files).
- All agents report status to the orchestrator. Cross-agent questions routed through orchestrator.
