mock_provider "aws" {
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
  project_name      = "ProjectCerberus"
  environment       = "dev"
  input_bucket_arn  = "arn:aws:s3:::ProjectCerberus-dev-input"
  output_bucket_arn = "arn:aws:s3:::ProjectCerberus-dev-output"
  queue_arn         = "arn:aws:sqs:us-east-1:123456789012:ProjectCerberus-dev-jobs"
  table_arn         = "arn:aws:dynamodb:us-east-1:123456789012:table/ProjectCerberus-dev-jobs"
}

# ---------------------------------------------------------------------------
# Worker Role: name, trust policy, tags
# ---------------------------------------------------------------------------
run "worker_role" {
  command = apply

  assert {
    condition     = aws_iam_role.worker.name == "ProjectCerberus-dev-worker-role"
    error_message = "Worker role name must be 'ProjectCerberus-dev-worker-role', got '${aws_iam_role.worker.name}'"
  }
  assert {
    condition     = aws_iam_role.worker.tags["Purpose"] == "worker-execution"
    error_message = "Worker role tag Purpose must be 'worker-execution'"
  }

  # Trust policy: EC2 service can assume this role
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_role.worker.assume_role_policy).Statement :
      stmt.Effect == "Allow" &&
      contains(keys(stmt.Principal), "Service") &&
      stmt.Principal.Service == "ec2.amazonaws.com"
    ])
    error_message = "Worker role trust policy must allow EC2 service to assume the role"
  }
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_role.worker.assume_role_policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "sts:AssumeRole")
    ])
    error_message = "Worker role trust policy must include sts:AssumeRole action"
  }
}

# ---------------------------------------------------------------------------
# Frontend Role: name, trust policy, tags
# ---------------------------------------------------------------------------
run "frontend_role" {
  command = apply

  assert {
    condition     = aws_iam_role.frontend.name == "ProjectCerberus-dev-frontend-role"
    error_message = "Frontend role name must be 'ProjectCerberus-dev-frontend-role', got '${aws_iam_role.frontend.name}'"
  }
  assert {
    condition     = aws_iam_role.frontend.tags["Purpose"] == "frontend-dashboard"
    error_message = "Frontend role tag Purpose must be 'frontend-dashboard'"
  }

  # Trust policy: EC2 service can assume this role
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_role.frontend.assume_role_policy).Statement :
      stmt.Effect == "Allow" &&
      contains(keys(stmt.Principal), "Service") &&
      stmt.Principal.Service == "ec2.amazonaws.com"
    ])
    error_message = "Frontend role trust policy must allow EC2 service to assume the role"
  }
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_role.frontend.assume_role_policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "sts:AssumeRole")
    ])
    error_message = "Frontend role trust policy must include sts:AssumeRole action"
  }
}

# ---------------------------------------------------------------------------
# Worker Policy: actions and least-privilege
# ---------------------------------------------------------------------------
run "worker_policy_actions" {
  command = apply

  # Decode once in each assert (no locals in .tftest.hcl)
  # Check that each required action is present
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.worker_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "s3:GetObject")
    ])
    error_message = "Worker policy must allow s3:GetObject for input bucket reads"
  }
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.worker_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "s3:PutObject")
    ])
    error_message = "Worker policy must allow s3:PutObject for output bucket writes"
  }
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.worker_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "sqs:ReceiveMessage")
    ])
    error_message = "Worker policy must allow sqs:ReceiveMessage"
  }
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.worker_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "sqs:DeleteMessage")
    ])
    error_message = "Worker policy must allow sqs:DeleteMessage"
  }
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.worker_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "sqs:GetQueueAttributes")
    ])
    error_message = "Worker policy must allow sqs:GetQueueAttributes"
  }
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.worker_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "dynamodb:PutItem")
    ])
    error_message = "Worker policy must allow dynamodb:PutItem"
  }
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.worker_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "dynamodb:UpdateItem")
    ])
    error_message = "Worker policy must allow dynamodb:UpdateItem"
  }
  # Tracked added by worker but not in original spec: dynamodb:GetItem
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.worker_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "dynamodb:GetItem")
    ])
    error_message = "Worker policy must allow dynamodb:GetItem"
  }
  # Verify exactly 4 statements
  assert {
    condition     = length(jsondecode(aws_iam_policy.worker_main.policy).Statement) == 4
    error_message = "Worker policy must have exactly 4 statements (S3 read, S3 write, SQS, DynamoDB), got ${length(jsondecode(aws_iam_policy.worker_main.policy).Statement)}"
  }
}

# ---------------------------------------------------------------------------
# Frontend Policy: actions and least-privilege
# ---------------------------------------------------------------------------
run "frontend_policy_actions" {
  command = apply

  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.frontend_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "sqs:SendMessage")
    ])
    error_message = "Frontend policy must allow sqs:SendMessage"
  }
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.frontend_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "dynamodb:Query")
    ])
    error_message = "Frontend policy must allow dynamodb:Query"
  }
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.frontend_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "dynamodb:GetItem")
    ])
    error_message = "Frontend policy must allow dynamodb:GetItem"
  }
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.frontend_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "s3:PutObject")
    ])
    error_message = "Frontend policy must allow s3:PutObject for video uploads"
  }
  assert {
    condition     = length(jsondecode(aws_iam_policy.frontend_main.policy).Statement) == 3
    error_message = "Frontend policy must have exactly 3 statements (S3 upload, SQS send, DynamoDB read), got ${length(jsondecode(aws_iam_policy.frontend_main.policy).Statement)}"
  }
}

# ---------------------------------------------------------------------------
# Security: no wildcard actions, no admin-level permissions
# ---------------------------------------------------------------------------
run "no_wildcard_actions" {
  command = apply

  assert {
    condition = !anytrue([
      for stmt in jsondecode(aws_iam_policy.worker_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "*")
    ])
    error_message = "Worker policy must not use wildcard actions — each action must be explicitly named"
  }

  assert {
    condition = !anytrue([
      for stmt in jsondecode(aws_iam_policy.frontend_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "*")
    ])
    error_message = "Frontend policy must not use wildcard actions — each action must be explicitly named"
  }
}

run "no_wildcard_resources" {
  command = apply

  # Check no statement has resource = "*" (wildcard all resources)
  assert {
    condition = !anytrue([
      for stmt in jsondecode(aws_iam_policy.worker_main.policy).Statement :
      try(stmt.Resource == "*", false)
    ])
    error_message = "Worker policy must not scope any statement to wildcard resource '*'"
  }

  assert {
    condition = !anytrue([
      for stmt in jsondecode(aws_iam_policy.frontend_main.policy).Statement :
      try(stmt.Resource == "*", false)
    ])
    error_message = "Frontend policy must not scope any statement to wildcard resource '*'"
  }
}

run "no_admin_level_permissions" {
  command = apply

  # Verify that no action in either policy contains "Admin" or "*"
  assert {
    condition = alltrue(concat(
      [for stmt in jsondecode(aws_iam_policy.worker_main.policy).Statement :
       !can(regex("(?i)admin", join(",", try(tolist(stmt.Action), [try(stmt.Action, "")]))))
      ],
      [for stmt in jsondecode(aws_iam_policy.frontend_main.policy).Statement :
       !can(regex("(?i)admin", join(",", try(tolist(stmt.Action), [try(stmt.Action, "")]))))
      ]
    ))
    error_message = "Neither worker nor frontend policy should contain admin-level actions"
  }
}

# ---------------------------------------------------------------------------
# Policy references correct resource ARNs from module inputs
# ---------------------------------------------------------------------------
run "worker_policy_references_correct_arns" {
  command = apply

  # Worker: S3 GetObject should reference input_bucket_arn
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.worker_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "s3:GetObject") &&
      try(length(stmt.Resource), 0) > 0 &&
      stmt.Resource[0] == var.input_bucket_arn &&
      (length(stmt.Resource) < 2 || stmt.Resource[1] == "/*")
    ])
    error_message = "Worker S3 GetObject must reference input_bucket_arn (${var.input_bucket_arn}) and allow '/*' objects"
  }

  # Worker: S3 PutObject should reference output_bucket_arn
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.worker_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "s3:PutObject") &&
      try(length(stmt.Resource), 0) > 0 &&
      stmt.Resource[0] == var.output_bucket_arn &&
      (length(stmt.Resource) < 2 || stmt.Resource[1] == "/*")
    ])
    error_message = "Worker S3 PutObject must reference output_bucket_arn (${var.output_bucket_arn}) and allow '/*' objects"
  }

  # Worker: SQS actions should reference queue_arn
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.worker_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "sqs:ReceiveMessage") &&
      try(stmt.Resource, "") == var.queue_arn
    ])
    error_message = "Worker SQS actions must reference queue_arn (${var.queue_arn})"
  }

  # Worker: DynamoDB actions should reference table_arn
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.worker_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "dynamodb:PutItem") &&
      try(stmt.Resource, "") == var.table_arn
    ])
    error_message = "Worker DynamoDB actions must reference table_arn (${var.table_arn})"
  }
}

run "frontend_policy_references_correct_arns" {
  command = apply

  # Frontend: S3 PutObject should reference input_bucket_arn
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.frontend_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "s3:PutObject") &&
      try(length(stmt.Resource), 0) > 0 &&
      stmt.Resource[0] == var.input_bucket_arn
    ])
    error_message = "Frontend S3 PutObject must reference input_bucket_arn (${var.input_bucket_arn})"
  }

  # Frontend: SQS SendMessage should reference queue_arn
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.frontend_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "sqs:SendMessage") &&
      try(stmt.Resource, "") == var.queue_arn
    ])
    error_message = "Frontend SQS SendMessage must reference queue_arn (${var.queue_arn})"
  }

  # Frontend: DynamoDB actions should reference table_arn
  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_policy.frontend_main.policy).Statement :
      contains(try(tolist(stmt.Action), [stmt.Action]), "dynamodb:Query") &&
      try(stmt.Resource, "") == var.table_arn
    ])
    error_message = "Frontend DynamoDB Query must reference table_arn (${var.table_arn})"
  }
}

# ---------------------------------------------------------------------------
# Role-Policy Attachments
# ---------------------------------------------------------------------------
run "role_policy_attachments" {
  command = apply

  assert {
    condition     = aws_iam_role_policy_attachment.worker_attach.role == aws_iam_role.worker.name
    error_message = "Worker policy must be attached to the worker role"
  }
  assert {
    condition     = aws_iam_role_policy_attachment.frontend_attach.role == aws_iam_role.frontend.name
    error_message = "Frontend policy must be attached to the frontend role"
  }
}

# ---------------------------------------------------------------------------
# Module Outputs
# ---------------------------------------------------------------------------
run "module_outputs" {
  command = apply

  assert {
    condition     = can(output.worker_role_arn) && can(regex("^arn:", output.worker_role_arn))
    error_message = "Module must export valid ARN as worker_role_arn"
  }
  assert {
    condition     = can(output.frontend_role_arn) && can(regex("^arn:", output.frontend_role_arn))
    error_message = "Module must export valid ARN as frontend_role_arn"
  }
}
