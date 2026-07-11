module "input_bucket" {
  source           = "./modules/s3-input"
  project_name     = var.project_name
  environment      = var.environment
  dashboard_origin = var.dashboard_origin
}

module "output_bucket" {
  source       = "./modules/s3-output"
  project_name = var.project_name
  environment  = var.environment
}

module "job_queue" {
  source       = "./modules/sqs"
  project_name = var.project_name
  environment  = var.environment
}

module "jobs_table" {
  source       = "./modules/dynamodb"
  project_name = var.project_name
  environment  = var.environment
}

module "iam_roles" {
  source            = "./modules/iam"
  project_name      = var.project_name
  environment       = var.environment
  input_bucket_arn  = module.input_bucket.bucket_arn
  output_bucket_arn = module.output_bucket.bucket_arn
  queue_arn         = module.job_queue.queue_arn
  table_arn         = module.jobs_table.table_arn
}