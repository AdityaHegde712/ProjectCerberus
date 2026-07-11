output "input_bucket_id" {
  description = "S3 input bucket ID"
  value       = module.input_bucket.bucket_id
}

output "input_bucket_arn" {
  description = "S3 input bucket ARN"
  value       = module.input_bucket.bucket_arn
}

output "output_bucket_id" {
  description = "S3 output bucket ID"
  value       = module.output_bucket.bucket_id
}

output "output_bucket_arn" {
  description = "S3 output bucket ARN"
  value       = module.output_bucket.bucket_arn
}

output "job_queue_url" {
  description = "SQS job queue URL"
  value       = module.job_queue.queue_id
}

output "job_queue_arn" {
  description = "SQS job queue ARN"
  value       = module.job_queue.queue_arn
}

output "dlq_arn" {
  description = "SQS DLQ ARN"
  value       = module.job_queue.dlq_arn
}

output "jobs_table_name" {
  description = "DynamoDB table name"
  value       = module.jobs_table.table_name
}

output "jobs_table_arn" {
  description = "DynamoDB table ARN"
  value       = module.jobs_table.table_arn
}

output "worker_role_arn" {
  description = "Worker IAM role ARN"
  value       = module.iam_roles.worker_role_arn
}

output "frontend_role_arn" {
  description = "Frontend IAM role ARN"
  value       = module.iam_roles.frontend_role_arn
}