# HANDOFF — Orchestrator Briefing

## Project: Distributed Batch Inference Pipeline

The architect planning phase is complete. The Owner has confirmed the plan.

## Current State

- **Phase 0 (Environment Setup)**: ✅ COMPLETED by Owner
  - Terraform installed
  - AWS CLI configured (us-east-1, AdminAccess IAM user)
  - Git repo initialized + pushed to GitHub
  - All tools verified
- **Next phase**: Phase 1 — Core Worker Logic + TDD

## Where to Find Everything

| Artifact | Location |
|---|---|
| Full phased plan | `.agent-tasks/architect/PLAN.md` |
| Task list (68 tasks) | `.agent-tasks/architect/TASKS.md` |
| Agent team roster | `.agent-tasks/architect/AGENT_TEAM.md` |
| Current status + decisions | `.agent-tasks/architect/STATUS.md` |
| Per-agent plans | `.agent-tasks/<agent>/PLAN.md` |
| Prerequisites guide | `PREREQUISITES.md` (already completed) |

## Version Structure

The project has 3 versions within a single plan:

| Version | Phases | Compute | CI/CD |
|---|---|---|---|
| **v1.0** | 1 → 2 → 3 → 4 | EC2 t2.micro | None (manual) |
| **v2.0** | → 5 | Fargate + ECS | v1: image build, v2: frontend deploy |
| **v3.0** | → 6 | Lambda | v3: +Terraform auto-apply |
| **Final** | → 7 | — | Docs finalization |

## Key Handoff Notes

1. **Phase 1 is locked TDD**: @app/tester writes ALL unit tests first, confirms they fail (Red), signals orchestrator. Then implementation agents code. Then tester re-runs and reports.

2. **@app/tester does NOT modify implementation** — write + run only.

3. **Doc timeline**: Initial docs (architecture diagram, deployment guide, README) created in Phase 3-4. Cost research by @util/research-analyst during v2.0/v3.0. Phase 7 is finalization + corrections.

4. **Backend API** (Phase 3) = Lambda + API Gateway (separate from worker Lambda in Phase 6).

5. **Canvas rendering** (Phase 3.7) requires manual JavaScript drawing — Canvas is a blank API.

6. **YOLO bbox format**: [x_center, y_center, width, height] normalized 0-1 (NOT COCO format).

7. **Terraform state**: Local during v1.0-v2.0. Migrate to S3+DynamoDB in Phase 6 (needed for CI/CD auto-apply).

8. **CI/CD secrets**: GitHub repo needs AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY configured as repository secrets before CI/CD workflows run (Phase 5+).

9. **Destroy discipline**: Run `terraform destroy` after every session to avoid free-tier overage.

## Execution Order

```
Phase 1 (Core TDD) → Phase 2 (Infra) → Phase 3 (Dashboard) → Phase 4 (EC2)
    → [v1.0 milestone] → Phase 5 (Fargate + CI/CD) → [v2.0 milestone]
    → Phase 6 (Lambda + CI/CD v3) → [v3.0 milestone] → Phase 7 (Docs)
```

Begin with Phase 1.
