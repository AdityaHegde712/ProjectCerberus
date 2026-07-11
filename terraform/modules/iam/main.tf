variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "input_bucket_arn" {
  description = "ARN of the S3 input bucket"
  type        = string
}

variable "output_bucket_arn" {
  description = "ARN of the S3 output bucket"
  type        = string
}

variable "queue_arn" {
  description = "ARN of the SQS job queue"
  type        = string
}

variable "table_arn" {
  description = "ARN of the DynamoDB jobs table"
  type        = string
}

resource "aws_iam_role" "worker" {
  name = "${var.project_name}-${var.environment}-worker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "worker-execution"
  }
}

resource "aws_iam_role" "frontend" {
  name = "${var.project_name}-${var.environment}-frontend-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "frontend-dashboard"
  }
}

resource "aws_iam_policy" "worker_main" {
  name = "${var.project_name}-${var.environment}-worker-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${var.input_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${var.output_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.queue_arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem"
        ]
        Resource = var.table_arn
      }
    ]
  })

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "worker-permissions"
  }
}

resource "aws_iam_policy" "frontend_main" {
  name = "${var.project_name}-${var.environment}-frontend-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${var.input_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = var.queue_arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Query",
          "dynamodb:GetItem"
        ]
        Resource = var.table_arn
      }
    ]
  })

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "frontend-permissions"
  }
}

resource "aws_iam_role_policy_attachment" "worker_attach" {
  role       = aws_iam_role.worker.name
  policy_arn = aws_iam_policy.worker_main.arn
}

resource "aws_iam_role_policy_attachment" "frontend_attach" {
  role       = aws_iam_role.frontend.name
  policy_arn = aws_iam_policy.frontend_main.arn
}

output "worker_role_arn" {
  value = aws_iam_role.worker.arn
}

output "frontend_role_arn" {
  value = aws_iam_role.frontend.arn
}