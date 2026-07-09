# PLAN — @app/technical-writer

**Role**: Documentation, diagrams, comparisons.

## Tasks

### 7.1 — Architecture diagram

- Format: Mermaid (embeddable in README) + draw.io or Excalidraw file for editable version
- Show: S3 → SQS → Worker(3 variants) → S3 + DynamoDB → Dashboard
- 3 worker variants as sub-diagrams or callouts

### 7.2 — Cost comparison document

Structured table:

| Dimension | EC2 | Fargate | Lambda |
|---|---|---|---|
| Setup complexity | | | |
| Cold start time | | | |
| Latency per 100 frames | | | |
| Cost per 1,000 jobs | | | |
| Operational burden | | | |
| Best for... | | | |

Reference notes from @app/backend-dev's comparison files (task 5.8, 6.8).

### 7.3 — Deployment guide (beginner-oriented)

- Audience: someone who knows basic programming but is new to AWS
- Step-by-step: from PREREQUISITES.md through full pipeline deployment
- Screenshots or CLI command snippets
- Separate sections for EC2 / Fargate / Lambda paths

### 7.4 — README.md

- Project overview, architecture, quick start, usage, teardown
- Badges (CI/CD status, etc.)
- Reference to architecture diagram

### 7.5 — Teardown instructions

- `terraform destroy` checklist
- S3 bucket empty before destroy
- CloudWatch log group cleanup
- Cost verification (check AWS Billing → no lingering resources)

### 7.6 — Final status report

- What was built
- Key learnings (EC2 vs Fargate vs Lambda tradeoffs)
- What could be improved

## Output Files

```
docs/
  architecture-diagram.md   (Mermaid)
  architecture-diagram.drawio
  cost-comparison.md
  deployment-guide.md
  teardown-checklist.md

README.md
```
