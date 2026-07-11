mock_provider "aws" {
  mock_resource "aws_s3_bucket" {
    defaults = {
      arn = "arn:aws:s3:::mock-input-bucket"
    }
  }
  mock_resource "aws_s3_bucket_cors_configuration" {
    defaults = {
      cors_rule = [{
        allowed_headers = ["*"]
        allowed_methods = ["PUT", "POST"]
        allowed_origins = ["https://dashboard.example.com"]
        expose_headers  = ["ETag"]
        max_age_seconds = 3000
      }]
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
  project_name     = "ProjectCerberus"
  environment      = "dev"
  dashboard_origin = "https://dashboard.example.com"
}

# ---------------------------------------------------------------------------
# S3 Input Bucket: name, tags, versioning, encryption, CORS
# ---------------------------------------------------------------------------
run "bucket_name_and_tags" {
  command = apply

  assert {
    condition     = aws_s3_bucket.input.bucket == "projectcerberus-dev-input"
    error_message = "Input bucket name must be 'projectcerberus-dev-input', got '${aws_s3_bucket.input.bucket}'"
  }
  assert {
    condition     = aws_s3_bucket.input.tags["Project"] == "ProjectCerberus"
    error_message = "Input bucket tag Project must be 'ProjectCerberus', got '${try(aws_s3_bucket.input.tags["Project"], "<missing>")}'"
  }
  assert {
    condition     = aws_s3_bucket.input.tags["Environment"] == "dev"
    error_message = "Input bucket tag Environment must be 'dev', got '${try(aws_s3_bucket.input.tags["Environment"], "<missing>")}'"
  }
  assert {
    condition     = aws_s3_bucket.input.tags["Purpose"] == "video-input"
    error_message = "Input bucket tag Purpose must be 'video-input', got '${try(aws_s3_bucket.input.tags["Purpose"], "<missing>")}'"
  }
}

run "versioning_enabled" {
  command = apply

  assert {
    condition     = aws_s3_bucket_versioning.input.versioning_configuration[0].status == "Enabled"
    error_message = "Input bucket versioning must be 'Enabled', got '${try(aws_s3_bucket_versioning.input.versioning_configuration[0].status, "<missing>")}'"
  }
}

run "encryption_aes256" {
  command = apply

  assert {
    condition     = try(one(aws_s3_bucket_server_side_encryption_configuration.input.rule).apply_server_side_encryption_by_default[0].sse_algorithm, "") == "AES256"
    error_message = "Input bucket SSE algorithm must be 'AES256', got '${try(one(aws_s3_bucket_server_side_encryption_configuration.input.rule).apply_server_side_encryption_by_default[0].sse_algorithm, "<missing>")}'"
  }
}

run "public_access_block" {
  command = apply

  assert {
    condition     = aws_s3_bucket_public_access_block.input.block_public_acls == true
    error_message = "Input bucket must block public ACLs"
  }
  assert {
    condition     = aws_s3_bucket_public_access_block.input.block_public_policy == true
    error_message = "Input bucket must block public bucket policies"
  }
  assert {
    condition     = aws_s3_bucket_public_access_block.input.restrict_public_buckets == true
    error_message = "Input bucket must restrict public bucket access"
  }
}

run "cors_configuration" {
  command = plan

  assert {
    condition     = contains(one(aws_s3_bucket_cors_configuration.input.cors_rule).allowed_methods, "PUT")
    error_message = "Input bucket CORS must allow PUT method"
  }

  assert {
    condition     = contains(one(aws_s3_bucket_cors_configuration.input.cors_rule).allowed_methods, "POST")
    error_message = "Input bucket CORS must allow POST method"
  }

  assert {
    condition     = contains(one(aws_s3_bucket_cors_configuration.input.cors_rule).allowed_origins, "https://dashboard.example.com")
    error_message = "Input bucket CORS must allow origin 'https://dashboard.example.com'"
  }

  assert {
    condition     = contains(one(aws_s3_bucket_cors_configuration.input.cors_rule).expose_headers, "ETag")
    error_message = "Input bucket CORS must expose 'ETag' header"
  }

  assert {
    condition     = one(aws_s3_bucket_cors_configuration.input.cors_rule).max_age_seconds == 3000
    error_message = "Input bucket CORS max_age_seconds must be 3000"
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
