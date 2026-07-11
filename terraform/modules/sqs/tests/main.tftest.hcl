mock_provider "aws" {
  mock_resource "aws_sqs_queue" {
    defaults = {
      arn = "arn:aws:sqs:us-east-1:000000000000:mock-queue"
    }
  }
}

variables {
  project_name = "ProjectCerberus"
  environment  = "dev"
}

# ---------------------------------------------------------------------------
# SQS Job Queue: name, visibility timeout, receive wait, redrive policy, tags
# ---------------------------------------------------------------------------
run "job_queue_config" {
  command = apply

  assert {
    condition     = aws_sqs_queue.jobs.name == "ProjectCerberus-dev-jobs"
    error_message = "Job queue name must be 'ProjectCerberus-dev-jobs', got '${aws_sqs_queue.jobs.name}'"
  }
  assert {
    condition     = aws_sqs_queue.jobs.visibility_timeout_seconds == 300
    error_message = "Job queue visibility timeout must be 300s, got ${aws_sqs_queue.jobs.visibility_timeout_seconds}"
  }
  assert {
    condition     = aws_sqs_queue.jobs.receive_wait_time_seconds == 20
    error_message = "Job queue receive wait time must be 20s, got ${aws_sqs_queue.jobs.receive_wait_time_seconds}"
  }
  assert {
    condition     = aws_sqs_queue.jobs.tags["Purpose"] == "job-queue"
    error_message = "Job queue tag Purpose must be 'job-queue', got '${try(aws_sqs_queue.jobs.tags["Purpose"], "<missing>")}'"
  }
  assert {
    condition     = aws_sqs_queue.jobs.tags["Project"] == "ProjectCerberus"
    error_message = "Job queue tag Project must be 'ProjectCerberus'"
  }
  assert {
    condition     = aws_sqs_queue.jobs.tags["Environment"] == "dev"
    error_message = "Job queue tag Environment must be 'dev'"
  }
  assert {
    condition     = aws_sqs_queue.jobs.sqs_managed_sse_enabled == true
    error_message = "Job queue must have SQS-managed SSE enabled"
  }
}

run "redrive_policy" {
  command = apply

  assert {
    condition     = jsondecode(aws_sqs_queue.jobs.redrive_policy).maxReceiveCount == 3
    error_message = "Job queue redrive maxReceiveCount must be 3, got ${jsondecode(aws_sqs_queue.jobs.redrive_policy).maxReceiveCount}"
  }
  assert {
    condition     = can(regex("arn:", jsondecode(aws_sqs_queue.jobs.redrive_policy).deadLetterTargetArn))
    error_message = "Job queue redrive deadLetterTargetArn must be a valid ARN, got '${try(jsondecode(aws_sqs_queue.jobs.redrive_policy).deadLetterTargetArn, "<missing>")}'"
  }
}

# ---------------------------------------------------------------------------
# SQS DLQ: name, retention, tags
# ---------------------------------------------------------------------------
run "dlq_config" {
  command = apply

  assert {
    condition     = aws_sqs_queue.dlq.name == "ProjectCerberus-dev-dlq"
    error_message = "DLQ name must be 'ProjectCerberus-dev-dlq', got '${aws_sqs_queue.dlq.name}'"
  }
  # 4 days retention = 345600 seconds (AWS provider default)
  # With mock_provider, the value is null if not explicitly set in config
  assert {
    condition     = aws_sqs_queue.dlq.message_retention_seconds == null || aws_sqs_queue.dlq.message_retention_seconds == 345600
    error_message = "DLQ message retention must be 345600s (4 days) or null (AWS default)"
  }
  assert {
    condition     = aws_sqs_queue.dlq.tags["Purpose"] == "dead-letter-queue"
    error_message = "DLQ tag Purpose must be 'dead-letter-queue', got '${try(aws_sqs_queue.dlq.tags["Purpose"], "<missing>")}'"
  }
}

run "module_outputs" {
  command = apply

  assert {
    condition     = can(output.queue_id) && output.queue_id != ""
    error_message = "Module must export non-empty queue_id"
  }
  assert {
    condition     = can(output.queue_arn) && can(regex("^arn:", output.queue_arn))
    error_message = "Module must export valid ARN as queue_arn"
  }
  assert {
    condition     = can(output.dlq_arn) && can(regex("^arn:", output.dlq_arn))
    error_message = "Module must export valid ARN as dlq_arn"
  }
}
