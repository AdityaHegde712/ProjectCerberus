mock_provider "aws" {
  mock_resource "aws_s3_bucket" {
    defaults = {
      arn = "arn:aws:s3:::mock-output-bucket"
    }
  }
  mock_resource "aws_s3_bucket_public_access_block" {
    defaults = {
      block_public_acls       = true
      block_public_policy     = true
      ignore_public_acls      = true
      restrict_public_buckets = true
    }
  }
}

variables {
  project_name = "ProjectCerberus"
  environment  = "dev"
}

# ---------------------------------------------------------------------------
# S3 Output Bucket: name, tags, encryption, versioning, public access block
# ---------------------------------------------------------------------------
run "bucket_name_and_tags" {
  command = apply

  assert {
    condition     = aws_s3_bucket.output.bucket == "projectcerberus-dev-output"
    error_message = "Output bucket name must be 'projectcerberus-dev-output', got '${aws_s3_bucket.output.bucket}'"
  }
  assert {
    condition     = aws_s3_bucket.output.tags["Project"] == "ProjectCerberus"
    error_message = "Output bucket tag Project must be 'ProjectCerberus', got '${try(aws_s3_bucket.output.tags["Project"], "<missing>")}'"
  }
  assert {
    condition     = aws_s3_bucket.output.tags["Environment"] == "dev"
    error_message = "Output bucket tag Environment must be 'dev', got '${try(aws_s3_bucket.output.tags["Environment"], "<missing>")}'"
  }
  assert {
    condition     = aws_s3_bucket.output.tags["Purpose"] == "detection-results"
    error_message = "Output bucket tag Purpose must be 'detection-results', got '${try(aws_s3_bucket.output.tags["Purpose"], "<missing>")}'"
  }
}

run "encryption_aes256" {
  command = apply

  assert {
    condition     = try(one(aws_s3_bucket_server_side_encryption_configuration.output.rule).apply_server_side_encryption_by_default[0].sse_algorithm, "") == "AES256"
    error_message = "Output bucket SSE algorithm must be 'AES256', got '${try(one(aws_s3_bucket_server_side_encryption_configuration.output.rule).apply_server_side_encryption_by_default[0].sse_algorithm, "<missing>")}'"
  }
}

run "versioning_enabled" {
  command = apply

  assert {
    condition     = one(aws_s3_bucket_versioning.output.versioning_configuration).status == "Enabled"
    error_message = "Output bucket versioning must be 'Enabled', got '${try(one(aws_s3_bucket_versioning.output.versioning_configuration).status, "<missing>")}'"
  }
}

run "public_access_block" {
  command = apply

  assert {
    condition     = aws_s3_bucket_public_access_block.output.block_public_acls == true
    error_message = "Output bucket must block public ACLs"
  }
  assert {
    condition     = aws_s3_bucket_public_access_block.output.block_public_policy == true
    error_message = "Output bucket must block public bucket policies"
  }
}

run "module_outputs" {
  command = apply

  assert {
    condition     = can(output.bucket_id) && output.bucket_id != ""
    error_message = "Module must export non-empty bucket_id"
  }
  assert {
    condition     = can(output.bucket_arn) && can(regex("^arn:", output.bucket_arn))
    error_message = "Module must export valid ARN as bucket_arn, got '${try(output.bucket_arn, "<missing>")}'"
  }
}
