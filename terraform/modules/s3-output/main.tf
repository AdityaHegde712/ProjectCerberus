variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

resource "aws_s3_bucket" "output" {
  bucket = "${var.project_name}-${var.environment}-output"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "detection-results"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "output" {
  bucket = aws_s3_bucket.output.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

output "bucket_id" {
  value = aws_s3_bucket.output.id
}

output "bucket_arn" {
  value = aws_s3_bucket.output.arn
}