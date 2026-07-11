mock_provider "aws" {
  mock_resource "aws_dynamodb_table" {
    defaults = {
      arn = "arn:aws:dynamodb:us-east-1:000000000000:table/mock-table"
    }
  }
}

variables {
  project_name = "ProjectCerberus"
  environment  = "dev"
}

# ---------------------------------------------------------------------------
# DynamoDB Table: name, billing mode, hash key, attribute, TTL, tags
# ---------------------------------------------------------------------------
run "table_config" {
  command = apply

  assert {
    condition     = aws_dynamodb_table.jobs.name == "ProjectCerberus-dev-jobs"
    error_message = "Table name must be 'ProjectCerberus-dev-jobs', got '${aws_dynamodb_table.jobs.name}'"
  }
  assert {
    condition     = aws_dynamodb_table.jobs.billing_mode == "PAY_PER_REQUEST"
    error_message = "Billing mode must be PAY_PER_REQUEST, got '${aws_dynamodb_table.jobs.billing_mode}'"
  }
  assert {
    condition     = aws_dynamodb_table.jobs.hash_key == "jobId"
    error_message = "Hash key must be 'jobId', got '${aws_dynamodb_table.jobs.hash_key}'"
  }
  assert {
    condition     = length(aws_dynamodb_table.jobs.attribute) > 0
    error_message = "Table must define at least one attribute"
  }
  assert {
    condition     = length(aws_dynamodb_table.jobs.attribute) > 0 && try(one(aws_dynamodb_table.jobs.attribute).name, "") == "jobId"
    error_message = "First attribute name must be 'jobId'"
  }
  assert {
    condition     = length(aws_dynamodb_table.jobs.attribute) > 0 && try(one(aws_dynamodb_table.jobs.attribute).type, "") == "S"
    error_message = "First attribute type must be 'S' (string)"
  }
  assert {
    condition     = length(aws_dynamodb_table.jobs.ttl) > 0 && try(one(aws_dynamodb_table.jobs.ttl).attribute_name, "") == "ttl"
    error_message = "TTL attribute name must be 'ttl', got '${try(one(aws_dynamodb_table.jobs.ttl).attribute_name, "<missing>")}'"
  }
  assert {
    condition     = length(aws_dynamodb_table.jobs.ttl) > 0 && try(one(aws_dynamodb_table.jobs.ttl).enabled, false) == true
    error_message = "TTL must be enabled"
  }
  assert {
    condition     = length(aws_dynamodb_table.jobs.server_side_encryption) > 0 && try(one(aws_dynamodb_table.jobs.server_side_encryption).enabled, false) == true
    error_message = "Table must have server-side encryption enabled"
  }
  assert {
    condition     = length(aws_dynamodb_table.jobs.point_in_time_recovery) > 0 && try(one(aws_dynamodb_table.jobs.point_in_time_recovery).enabled, false) == true
    error_message = "Table must have point-in-time recovery enabled"
  }
}

run "table_tags" {
  command = apply

  assert {
    condition     = aws_dynamodb_table.jobs.tags["Purpose"] == "job-metadata"
    error_message = "Table tag Purpose must be 'job-metadata', got '${try(aws_dynamodb_table.jobs.tags["Purpose"], "<missing>")}'"
  }
  assert {
    condition     = aws_dynamodb_table.jobs.tags["Project"] == "ProjectCerberus"
    error_message = "Table tag Project must be 'ProjectCerberus'"
  }
  assert {
    condition     = aws_dynamodb_table.jobs.tags["Environment"] == "dev"
    error_message = "Table tag Environment must be 'dev'"
  }
}

run "module_outputs" {
  command = apply

  assert {
    condition     = can(output.table_name) && output.table_name != ""
    error_message = "Module must export non-empty table_name"
  }
  assert {
    condition     = can(output.table_arn) && can(regex("^arn:", output.table_arn))
    error_message = "Module must export valid ARN as table_arn, got '${try(output.table_arn, "<missing>")}'"
  }
}
