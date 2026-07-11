# STATUS — Distributed Batch Inference Pipeline

## Current State

- **Phase**: Phase 0 completed by Owner. Awaiting plan update confirmation.
- **Plan Version**: 1.1 (updated per Owner revision requests)
- **Date**: 2026-07-08

## Decision Log

| # | Decision | Choice | Rationale |
|---|---|---|---|
| D01 | Primary goal | Personal: learn cloud infra. Project: production-grade pipeline. | Two-track approach — learning as process, production as standard. |
| D02 | Video input size | Small clips (<30s, <50MB) | Keeps Lambda viable, fits free tier, reasonable for learning. |
| D03 | YOLO model | Off-the-shelf pretrained (YOLOv8n) | Focus on infra, not model tuning. |
| D04 | Dashboard scope | Polished web app (React+Vite+TS) | Wanted production quality. Framework preference satisfied. |
| D05 | Authentication | None | Single-user learning project. |
| D06 | Terraform state | Local → S3+DDB two-phase | Learn both patterns. Migrate when CI/CD auto-apply lands (v3.0). |
| D07 | Job schema | Minimal (jobId, status, videoKey, timestamps, workerType) | Keep it simple, focus on infra learning. |
| D08 | CI/CD scope | Iterative: image build → +frontend deploy → +Terraform auto-apply | Grows across versions: v2.0 (image+frontend), v3.0 (+TF). |
| D09 | AWS budget | Free tier only | Constraint forces efficient design + teardown discipline. |
| D10 | Dashboard hosting | S3 static website | Cheap, simple, real deployment. CloudFront optional later. |
| D11 | Testing rigor | Full Red-Green-Refactor TDD for core logic + integration tests | Tests as executable spec. Prevents regression across compute swaps. |
| D12 | Worker output | Detection JSON only | Lightweight, analysis-friendly. No FFmpeg dependency. |
| D13 | Result viewer | Table + single frame Canvas overlay | Educational — shows the data visually. Canvas requires manual JS bbox drawing. |
| D14 | Worker interface | Single `process_video()` function, 3 invokers | Core architectural pattern. Separation of logic from deployment. |
| D15 | Python toolchain | uv | Fast, modern, clean Docker builds. |
| D16 | AWS region | us-east-1 | Cheapest, most services, free tier eligible. |
| D17 | Repo structure | Monorepo in ProjectCerberus | Simpler management, single CI/CD. |
| D18 | Version structure | v1.0 (EC2) → v2.0 (Fargate) → v3.0 (Lambda) within single plan | Core shared, compute swapped. Pedagogical progression: raw VM → container → serverless. |
| D19 | Compute order | EC2 first (not Lambda) | EC2 is most transparent for learning. Avoid YOLO+Lambda cold-start pain as first experience. |
| D20 | Backend API | Lambda + API Gateway (Phase 3) | Separate from worker Lambda (Phase 6). Teaches Lambda early without conflating with worker swap. |
| D21 | YOLO bbox format | [x_center, y_center, width, height] normalized 0-1 | Standard YOLO output (not COCO's [x1,y1,x2,y2]). |
| D22 | Doc timeline | Initial docs Phase 3-4, research during v2/v3, finalize Phase 7 | Docs usable while building. Cost research by @util/research-analyst. |
| D23 | Diagram format | Mermaid + Excalidraw | Excalidraw uses JSON (agent-friendly), not draw.io XML. |
| D24 | Deployment guide | CLI snippets only | Agents cannot take screenshots. |
| D25 | Tester scope | Write + run tests only | No refactoring implementation. Tester workflow: write all → confirm fail → signal → wait → re-run → report. |

## Open Questions

None. All architectural decisions resolved.

## Blockers

None. Phase 0 completed by Owner.

## Blockers

None. Prerequisites documented in PREREQUISITES.md (manual steps before orchestrator).

## Next Steps

1. Owner confirms plan → enters execution queue
2. Owner completes PREREQUISITES.md steps
3. Orchestrator launches Phase 1 (TDD — tests first)
