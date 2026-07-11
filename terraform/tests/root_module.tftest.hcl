mock_provider "aws" {
  mock_resource "aws_s3_bucket" {
    defaults = {
      arn = "arn:aws:s3:::mock-bucket"
    }
  }
  mock_resource "aws_sqs_queue" {
    defaults = {
      arn = "arn:aws:sqs:us-east-1:000000000000:mock-queue"
    }
  }
  mock_resource "aws_dynamodb_table" {
    defaults = {
      arn = "arn:aws:dynamodb:us-east-1:000000000000:table/mock-table"
    }
  }
  mock_resource "aws_iam_role" {
    defaults = {
      arn = "arn:aws:iam::000000000000:role/mock-role"
    }
  }
  mock_resource "aws_iam_policy" {
    defaults = {
      arn = "arn:aws:iam::000000000000:policy/mock-policy"
    }
  }
}

variables {
  project_name     = "ProjectCerberus"
  environment      = "dev"
  dashboard_origin = "https://dashboard.example.com"
}

# ---------------------------------------------------------------------------
# Variable defaults
# ---------------------------------------------------------------------------
run "variable_defaults" {
  command = plan

  assert {
    condition     = var.project_name == "ProjectCerberus"
    error_message = "Default project_name must be 'ProjectCerberus', got '${var.project_name}'"
  }
  assert {
    condition     = var.environment == "dev"
    error_message = "Default environment must be 'dev', got '${var.environment}'"
  }
  assert {
    condition     = var.dashboard_origin == "https://dashboard.example.com"
    error_message = "Default dashboard_origin must be 'https://dashboard.example.com', got '${var.dashboard_origin}'"
  }
}

# ---------------------------------------------------------------------------
# Root module has exactly 11 outputs, wired from child modules
# In apply mode with mock_provider, all outputs have mock values.
# ---------------------------------------------------------------------------
run "all_eleven_outputs_exist" {
  command = apply

  assert {
    condition     = can(output.input_bucket_id) && output.input_bucket_id != ""
    error_message = "output.input_bucket_id must exist and be non-empty"
  }
  assert {
    condition     = can(output.input_bucket_arn) && can(regex("^arn:", output.input_bucket_arn))
    error_message = "output.input_bucket_arn must exist and be a valid ARN"
  }
  assert {
    condition     = can(output.output_bucket_id) && output.output_bucket_id != ""
    error_message = "output.output_bucket_id must exist and be non-empty"
  }
  assert {
    condition     = can(output.output_bucket_arn) && can(regex("^arn:", output.output_bucket_arn))
    error_message = "output.output_bucket_arn must exist and be a valid ARN"
  }
  assert {
    condition     = can(output.job_queue_url) && output.job_queue_url != ""
    error_message = "output.job_queue_url must exist and be non-empty"
  }
  assert {
    condition     = can(output.job_queue_arn) && can(regex("^arn:", output.job_queue_arn))
    error_message = "output.job_queue_arn must exist and be a valid ARN"
  }
  assert {
    condition     = can(output.dlq_arn) && can(regex("^arn:", output.dlq_arn))
    error_message = "output.dlq_arn must exist and be a valid ARN"
  }
  assert {
    condition     = can(output.jobs_table_name) && output.jobs_table_name != ""
    error_message = "output.jobs_table_name must exist and be non-empty"
  }
  assert {
    condition     = can(output.jobs_table_arn) && can(regex("^arn:", output.jobs_table_arn))
    error_message = "output.jobs_table_arn must exist and be a valid ARN"
  }
  assert {
    condition     = can(output.worker_role_arn) && can(regex("^arn:", output.worker_role_arn))
    error_message = "output.worker_role_arn must exist and be a valid ARN"
  }
  assert {
    condition     = can(output.frontend_role_arn) && can(regex("^arn:", output.frontend_role_arn))
    error_message = "output.frontend_role_arn must exist and be a valid ARN"
  }
}

# ---------------------------------------------------------------------------
# Output wire test: module outputs propagate correctly to root outputs
# (e.g., output.input_bucket_id matches module.input_bucket.bucket_id)
# ---------------------------------------------------------------------------
run "output_wiring" {
  command = apply

  assert {
    condition     = output.input_bucket_id == module.input_bucket.bucket_id
    error_message = "output.input_bucket_id must match module.input_bucket.bucket_id"
  }
  assert {
    condition     = output.input_bucket_arn == module.input_bucket.bucket_arn
    error_message = "output.input_bucket_arn must match module.input_bucket.bucket_arn"
  }
  assert {
    condition     = output.output_bucket_id == module.output_bucket.bucket_id
    error_message = "output.output_bucket_id must match module.output_bucket.bucket_id"
  }
  assert {
    condition     = output.job_queue_url == module.job_queue.queue_id
    error_message = "output.job_queue_url must match module.job_queue.queue_id"
  }
  assert {
    condition     = output.job_queue_arn == module.job_queue.queue_arn
    error_message = "output.job_queue_arn must match module.job_queue.queue_arn"
  }
  assert {
    condition     = output.dlq_arn == module.job_queue.dlq_arn
    error_message = "output.dlq_arn must match module.job_queue.dlq_arn"
  }
  assert {
    condition     = output.jobs_table_name == module.jobs_table.table_name
    error_message = "output.jobs_table_name must match module.jobs_table.table_name"
  }
  assert {
    condition     = output.worker_role_arn == module.iam_roles.worker_role_arn
    error_message = "output.worker_role_arn must match module.iam_roles.worker_role_arn"
  }
  assert {
    condition     = output.frontend_role_arn == module.iam_roles.frontend_role_arn
    error_message = "output.frontend_role_arn must match module.iam_roles.frontend_role_arn"
  }
}

# ---------------------------------------------------------------------------
# Negative tests: variable validation (placeholder — no validation blocks yet)
# ---------------------------------------------------------------------------
# NOTE: variables.tf has NO validation blocks. When they are added,
# add expect_failures run blocks here, for example:
#
#   run "rejects_empty_project_name" {
#     command = plan
#     variables { project_name = "" }
#     expect_failures = [var.project_name]
#   }
