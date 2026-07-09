# PLAN — @app/ops-expert

**Role**: Infrastructure (Terraform), containerization, CI/CD (GitHub Actions).

## Tasks

### Phase 2 — AWS Infrastructure v1

- 2.2: S3 input bucket with CORS policy (allow dashboard uploads)
- 2.3: S3 output bucket (worker writes results)
- 2.4: SQS standard queue + DLQ (visibility timeout = max expected job time)
- 2.5: DynamoDB table (partition key: `jobId`, TTL for auto-cleanup)
- 2.6: IAM roles (least-privilege per resource)
- 2.7: `terraform apply` + verify in console
- 2.8: Integration test script
- 2.9: Destroy workflow + docs

### Phase 4 — EC2

- 4.2: Terraform EC2 t2.micro + security group + user-data script
  - User-data: installs uv, clones repo (or pulls from GitHub), starts poller
  - Security group: SSH from your IP only, outbound internet

### Phase 5 — Fargate + CI/CD v1

- 5.1: Multi-stage Dockerfile (build deps → runtime, uv-based, ~200MB final image)
- 5.2: ECR repo Terraform module
- 5.3: Manual first push to ECR
- 5.4: GitHub Actions workflow — triggers on push to `worker/`, builds image, pushes to ECR
- 5.5: ECS cluster + Fargate task definition + service with SQS autoscaling
- 5.7: Deploy and verify

### Phase 6 — Lambda + CI/CD v2

- 6.2: Build+push Lambda container image (minimize size, test with lambda-runtime mock)
- 6.3: Lambda function + SQS event-source mapping (Terraform)
- 6.4: Update CI/CD — add Terraform auto-apply stage after image push
  - `terraform plan` → if changes, auto-apply
  - State migrated to S3+DDB backend

### Terraform Structure

```
terraform/
  main.tf
  variables.tf
  outputs.tf
  modules/
    s3-input/
    s3-output/
    sqs/
    dynamodb/
    iam/
    ec2/
    ecr/
    ecs/
    lambda/
  env/
    dev.tfvars
  backend.tf         -- local state initially, S3+DDB after migration
```

### CI/CD Structure

```
.github/workflows/
  worker-build.yml       -- Build + push worker image (Phase 5+)
  terraform-apply.yml    -- Terraform plan + apply (Phase 6+)
  frontend-deploy.yml    -- Build + deploy frontend (Phase 6+, optional)
```

## Verification

- `terraform apply` creates all resources without errors
- `terraform destroy` removes all resources cleanly
- GitHub Actions workflows run on push
