variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

resource "aws_sqs_queue" "dlq" {
  name = "${var.project_name}-${var.environment}-dlq"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "dead-letter-queue"
  }
}

resource "aws_sqs_queue" "jobs" {
  name                       = "${var.project_name}-${var.environment}-jobs"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 1209600
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "job-queue"
  }
}

output "queue_id" {
  value = aws_sqs_queue.jobs.id
}

output "queue_arn" {
  value = aws_sqs_queue.jobs.arn
}

output "dlq_arn" {
  value = aws_sqs_queue.dlq.arn
}