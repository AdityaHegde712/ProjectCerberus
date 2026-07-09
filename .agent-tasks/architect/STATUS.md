# STATUS — Distributed Batch Inference Pipeline

## Current State

- **Phase**: Pre-0 (Planning complete, awaiting Owner confirmation)
- **Plan Version**: 1.0
- **Date**: 2026-07-08

## Decision Log

| # | Decision | Choice | Rationale |
|---|---|---|---|
| D01 | Primary goal | Personal: learn cloud infra. Project: production-grade pipeline. | Two-track approach — learning as process, production as standard. |
| D02 | Video input size | Small clips (<30s, <50MB) | Keeps Lambda viable, fits free tier, reasonable for learning. |
| D03 | YOLO model | Off-the-shelf pretrained (YOLOv8n) | Focus on infra, not model tuning. |
| D04 | Dashboard scope | Polished web app (React+Vite+TS) | Wanted production quality. Framework preference satisfied. |
| D05 | Authentication | None | Single-user learning project. |
| D06 | Terraform state | Local → S3+DDB two-phase | Learn both patterns. Migrate when CI/CD lands. |
| D07 | Job schema | Minimal (jobId, status, videoKey, timestamps, workerType) | Keep it simple, focus on infra learning. |
| D08 | CI/CD scope | Iterative: worker image → +Terraform → +frontend deploy | Grows with project. Each addition is a learning step. |
| D09 | AWS budget | Free tier only | Constraint forces efficient design + teardown discipline. |
| D10 | Dashboard hosting | S3 static website | Cheap, simple, real deployment. CloudFront optional later. |
| D11 | Testing rigor | Full Red-Green-Refactor TDD for core logic + integration tests | Tests as executable spec. Prevents regression across compute swaps. |
| D12 | Worker output | Detection JSON only | Lightweight, analysis-friendly. No FFmpeg dependency. |
| D13 | Result viewer | Table + single frame Canvas overlay | Educational — shows the data visually. |
| D14 | Worker interface | Single `process_video()` function, 3 invokers | Core architectural pattern. Separation of logic from deployment. |
| D15 | Python toolchain | uv | Fast, modern, clean Docker builds. |
| D16 | AWS region | us-east-1 | Cheapest, most services, free tier eligible. |
| D17 | Repo structure | Monorepo in ProjectCerberus | Simpler management, single CI/CD. |

## Open Questions

None. All architectural decisions resolved.

## Blockers

None. Prerequisites documented in PREREQUISITES.md (manual steps before orchestrator).

## Next Steps

1. Owner confirms plan → enters execution queue
2. Owner completes PREREQUISITES.md steps
3. Orchestrator launches Phase 1 (TDD — tests first)
