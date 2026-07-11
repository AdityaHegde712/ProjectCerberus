# PLAN — @app/technical-writer

**Role**: Documentation, diagrams, comparisons.

**Note on doc timing**: Initial docs created early (after architecture finalized). Phase 7 is for updates/corrections, not creation.

## Tasks (Timeline-Ordered)

### [Phase 3 — Initial Architecture Diagram]
### 7.1 — Architecture diagram

- Format: Mermaid (embeddable in README) + **Excalidraw** file (JSON, agent-friendly) for editable version
- No draw.io (XML format is less agent-friendly)
- Show: S3 → SQS → Worker(3 variants) → S3 + DynamoDB → Dashboard
- 3 worker variants as sub-diagrams or callouts

### [Phase 4 — Initial Deploy Docs]
### 7.4 — README.md (initial)

- Project overview, architecture, quick start, usage, teardown
- Badges (CI/CD status, etc.)
- Reference to architecture diagram

### 7.3 — Deployment guide (initial — EC2 focused)

- Audience: someone who knows basic programming but is new to AWS
- Step-by-step: from PREREQUISITES.md through full pipeline deployment
- CLI command snippets only (agents cannot take screenshots)
- Separate sections: EC2 guide now, Fargate/Lambda added in later versions

### [During v2.0/v3.0 — Cost Research]
### 7.2 — Cost comparison document

- Research lead: **@util/research-analyst** gathers data on pricing, cold start benchmarks, latency
- @app/technical-writer formats into final document
- Structured table:

| Dimension | EC2 | Fargate | Lambda |
|---|---|---|---|
| Setup complexity | | | |
| Cold start time | | | |
| Latency per 100 frames | | | |
| Cost per 1,000 jobs | | | |
| Operational burden | | | |
| Best for... | | | |

- Reference notes from @app/backend-dev's comparison files (task 5.8, 6.8)
- Reference research from @util/research-analyst

### [Phase 7 — Final Updates]
### 7.5 — Teardown instructions

- `terraform destroy` checklist
- S3 bucket empty before destroy
- CloudWatch log group cleanup
- Cost verification (check AWS Billing → no lingering resources)

### 7.6 — Final status report

- What was built
- Key learnings (EC2 vs Fargate vs Lambda tradeoffs)
- What could be improved

### 7.7 — Update/correct initial docs

- Review architecture diagram — update if architecture changed during development
- Update deployment guide with Fargate/Lambda sections
- Update README with final badges, CI/CD status, cost comparison link

## Output Files

```
docs/
  architecture-diagram.md      (Mermaid — Phase 3)
  architecture-diagram.excalidraw  (Phase 3)
  deployment-guide.md          (Phase 4 initial, updated Phase 7)
  cost-comparison.md           (Phase 5-6 research, finalized Phase 7)
  teardown-checklist.md        (Phase 7)

README.md                      (Phase 4 initial, updated Phase 7)
```
