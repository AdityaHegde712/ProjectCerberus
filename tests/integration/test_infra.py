"""LOCKED — Integration tests for Phase 2 Terraform module outputs (Task 2.1).

These tests verify that the Terraform modules (once written) produce correct
resource naming, IAM least-privilege policies, S3 bucket configs, SQS queue
configs, and DynamoDB table schemas.

Tests parse .tf files using a lightweight HCL-like scanner.  Since no Terraform
files exist yet, every test currently fails (Red phase).  Do NOT modify these
test cases — they are locked to enforce correct infrastructure contracts.

Requires: pytest, pyhcl or built-in HCL parsing fallback.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

# ──────────────────────────────────────────────
# Constants — expected module layout
# ──────────────────────────────────────────────

TERRAFORM_ROOT = Path(__file__).resolve().parents[2] / "terraform"

EXPECTED_MODULES = {
    "s3-input": "terraform/modules/s3-input",
    "s3-output": "terraform/modules/s3-output",
    "sqs": "terraform/modules/sqs",
    "dynamodb": "terraform/modules/dynamodb",
    "iam": "terraform/modules/iam",
}

# ──────────────────────────────────────────────
# Helpers: lightweight HCL block parser
# ──────────────────────────────────────────────


def _read_tf_file(relative_path: str) -> str:
    """Read a .tf file relative to TERRAFORM_ROOT. Raises FileNotFoundError."""
    full_path = TERRAFORM_ROOT / relative_path
    if not full_path.exists():
        raise FileNotFoundError(
            f"Terraform file does not exist: {full_path}\n"
            f"Expected as part of Phase 2 implementation. "
            f"Create this file with the required resource definitions."
        )
    return full_path.read_text(encoding="utf-8")


def _find_resource_blocks(
    source: str, resource_type: str, resource_name: str
) -> List[Dict[str, Any]]:
    """Find all `resource "<resource_type>" "<resource_name>" { ... }` blocks.

    Returns a list of dicts, each containing the raw text of one block.
    """
    pattern = rf'resource\s+"{re.escape(resource_type)}"\s+"{re.escape(resource_name)}"\s*\{{'
    blocks: List[Dict[str, Any]] = []
    for match in re.finditer(pattern, source):
        block_text = _extract_balanced_brace_block(source, match.end())
        if block_text:
            blocks.append({"type": resource_type, "name": resource_name, "body": block_text})
    return blocks


def _find_data_blocks(
    source: str, data_type: str, data_name: str
) -> List[Dict[str, Any]]:
    """Find all `data "<data_type>" "<data_name>" { ... }` blocks."""
    pattern = rf'data\s+"{re.escape(data_type)}"\s+"{re.escape(data_name)}"\s*\{{'
    blocks: List[Dict[str, Any]] = []
    for match in re.finditer(pattern, source):
        block_text = _extract_balanced_brace_block(source, match.end())
        if block_text:
            blocks.append({"type": data_type, "name": data_name, "body": block_text})
    return blocks


def _find_module_blocks(source: str, module_name: str) -> List[Dict[str, Any]]:
    """Find all `module "<module_name>" { ... }` blocks."""
    pattern = rf'module\s+"{re.escape(module_name)}"\s*\{{'
    blocks: List[Dict[str, Any]] = []
    for match in re.finditer(pattern, source):
        block_text = _extract_balanced_brace_block(source, match.end())
        if block_text:
            blocks.append({"name": module_name, "body": block_text})
    return blocks


def _find_output_blocks(source: str, output_name: str) -> List[Dict[str, Any]]:
    """Find all `output "<output_name>" { ... }` blocks."""
    pattern = rf'output\s+"{re.escape(output_name)}"\s*\{{'
    blocks: List[Dict[str, Any]] = []
    for match in re.finditer(pattern, source):
        block_text = _extract_balanced_brace_block(source, match.end())
        if block_text:
            blocks.append({"name": output_name, "body": block_text})
    return blocks


def _extract_balanced_brace_block(source: str, start_pos: int) -> str:
    """Extract text from start_pos through the matching closing brace."""
    depth = 0
    in_string = False
    string_char = None
    for i in range(start_pos, len(source)):
        ch = source[i]
        if in_string:
            if ch == "\\":
                i += 1  # skip escaped char
                continue
            if ch == string_char:
                in_string = False
            continue
        if ch in ('"', "'"):
            in_string = True
            string_char = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[start_pos : i + 1]
    return ""


def _get_attr(block_body: str, attr_name: str) -> Optional[str]:
    """Extract the value of a top-level attribute from an HCL block body.

    Handles quoted and unquoted values, heredocs, and nested blocks.
    Returns the raw value string, or None if not found.
    """
    # Match: attr_name = "value"
    pattern = rf'^\s*{re.escape(attr_name)}\s*=\s*"([^"]*)"\s*$'
    for line in block_body.splitlines():
        m = re.match(pattern, line)
        if m:
            return m.group(1)
    # Match: attr_name = value  (unquoted, e.g. numbers, booleans, identifiers)
    pattern = rf'^\s*{re.escape(attr_name)}\s*=\s*([^\s{{"]+)\s*$'
    for line in block_body.splitlines():
        m = re.match(pattern, line)
        if m:
            return m.group(1)
    return None


def _get_map_attr(block_body: str, attr_name: str) -> Optional[Dict[str, str]]:
    """Extract a map/tag attribute like `tags = { Key = "val" }` spanning multiple lines."""
    pattern = rf'^\s*{re.escape(attr_name)}\s*=\s*\{{'
    for match in re.finditer(pattern, block_body, re.MULTILINE):
        brace_start = match.end() - 1
        map_text = _extract_balanced_brace_block(block_body, brace_start)
        if not map_text:
            continue
        result: Dict[str, str] = {}
        for kv_match in re.finditer(r'^\s*"([^"]*)"\s*=\s*"([^"]*)"\s*$', map_text, re.MULTILINE):
            result[kv_match.group(1)] = kv_match.group(2)
        return result
    return None


def _get_list_attr(block_body: str, attr_name: str) -> Optional[List[str]]:
    """Extract a list attribute like `attribute = ["a", "b"]`."""
    pattern = rf'^\s*{re.escape(attr_name)}\s*=\s*\[(.*?)\]'
    for match in re.finditer(pattern, block_body, re.MULTILINE | re.DOTALL):
        items_str = match.group(1)
        items = re.findall(r'"([^"]*)"', items_str)
        return items
    return None


def _block_contains(block_body: str, text: str) -> bool:
    """Check if a block body contains the given text (for policy documents, etc.)."""
    return text in block_body


def _has_nested_block(block_body: str, block_type: str, target_attr: Optional[str] = None) -> bool:
    """Check if a nested block (e.g., `cors_rule { ... }`) exists.

    Optionally checks if target_attr appears inside that block.
    """
    pattern = rf'\b{re.escape(block_type)}\s*\{{'
    for match in re.finditer(pattern, block_body):
        nested = _extract_balanced_brace_block(block_body, match.end())
        if not nested:
            continue
        if target_attr is None:
            return True
        if target_attr in nested:
            return True
    return False


def _parse_iam_policy(policy_json_str: str) -> Dict[str, Any]:
    """Parse a JSON IAM policy document string."""
    return json.loads(policy_json_str)


def _extract_policy_document(block_body: str) -> Optional[str]:
    """Extract the JSON string from a `policy = jsonencode({...})` or `policy = <<EOF ... EOF`."""
    # jsonencode case: policy = jsonencode({...})
    m = re.search(r'policy\s*=\s*jsonencode\(\s*(\{.*?\})\s*\)', block_body, re.DOTALL)
    if m:
        json_part = m.group(1)
        # Replace HCL-style comments before parsing
        json_part = re.sub(r'#.*', '', json_part)
        json_part = re.sub(r'//.*', '', json_part)
        return json_part
    # heredoc case: policy = <<EOF ... EOF
    m = re.search(r'policy\s*=\s*<<[-~]?(\w+)\s*\n(.*?)\n\s*\1\s*', block_body, re.DOTALL)
    if m:
        return m.group(2).strip()
    # direct string case
    m = re.search(r'policy\s*=\s*"(.+?)"', block_body, re.DOTALL)
    if m:
        return m.group(1)
    return None


def _resolve_hcl_json(block_body: str) -> Optional[Dict[str, Any]]:
    """Try to resolve an inline HCL JSON expression to a Python dict.

    Handles simple { key = value, ... } structures.
    """
    m = re.search(r'policy\s*=\s*jsonencode\(\s*(\{.*?\})\s*\)', block_body, re.DOTALL)
    if not m:
        return None
    raw = m.group(1)
    # Crude HCL→JSON conversion for simple cases
    # Replace = with :, add quotes around bare keys
    raw = re.sub(r'^\s*(\w+)\s*=', r'"\1": ', raw, flags=re.MULTILINE)
    # Replace trailing commas before }
    raw = re.sub(r',\s*}', '}', raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _assert_policy_statement(
    policy_doc: Optional[Dict[str, Any]],
    action_contains: Optional[str] = None,
    resource_contains: Optional[str] = None,
    effect: str = "Allow",
) -> None:
    """Assert that an IAM policy document contains a statement meeting criteria."""
    assert policy_doc is not None, "Policy document could not be parsed"
    statements = policy_doc.get("Statement", [])
    assert len(statements) > 0, "Policy must have at least one Statement"
    found = False
    for stmt in statements:
        if stmt.get("Effect") != effect:
            continue
        actions = stmt.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        resources = stmt.get("Resource", [])
        if isinstance(resources, str):
            resources = [resources]
        action_match = True
        resource_match = True
        if action_contains:
            action_match = any(action_contains in a for a in actions)
        if resource_contains:
            resource_match = any(resource_contains in r for r in resources)
        if action_match and resource_match:
            found = True
            break
    assert found, (
        f"No Statement found with effect={effect}, "
        f"action_contains={action_contains!r}, resource_contains={resource_contains!r}"
    )


def _resource_exists(relative_path: str) -> bool:
    """Check if a Terraform file exists."""
    return (TERRAFORM_ROOT / relative_path).exists()


# ══════════════════════════════════════════════
# Module: S3 Input Bucket
# ══════════════════════════════════════════════

@pytest.mark.integration
class TestS3InputBucket:
    """S3 input bucket — CORS policy for dashboard uploads."""

    MODULE_PATH = "modules/s3-input/main.tf"
    MODULE_DIR = "modules/s3-input"

    def test_module_directory_exists(self) -> None:
        """The s3-input module directory must exist."""
        path = TERRAFORM_ROOT / self.MODULE_DIR
        assert path.is_dir(), (
            f"Expected s3-input module directory: {path}\n"
            f"Create terraform/modules/s3-input/main.tf with the bucket resource."
        )

    def test_module_file_exists(self) -> None:
        """The s3-input module main.tf must exist."""
        assert _resource_exists(self.MODULE_PATH), (
            f"Missing Terraform module file: {TERRAFORM_ROOT / self.MODULE_PATH}\n"
            f"Define an S3 bucket resource for raw video uploads."
        )

    def test_bucket_resource_defined(self) -> None:
        """Must define an aws_s3_bucket resource."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_s3_bucket", "input")
        assert len(blocks) >= 1, (
            "No aws_s3_bucket 'input' resource found in s3-input module.\n"
            'Expected: resource "aws_s3_bucket" "input" { ... }'
        )

    def test_bucket_naming_convention(self) -> None:
        """Bucket name should follow project naming convention."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_s3_bucket", "input")
        assert len(blocks) >= 1, "Missing aws_s3_bucket 'input' resource."
        bucket_name = _get_attr(blocks[0]["body"], "bucket")
        # Bucket should be parameterized, not hardcoded — accept var reference
        if bucket_name:
            assert "var." in bucket_name or "local." in bucket_name, (
                f"Bucket name should use a variable reference, got: {bucket_name}"
            )

    def test_cors_policy_allows_dashboard_origin(self) -> None:
        """CORS rule must allow the dashboard origin with PUT/POST methods."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_s3_bucket", "input")
        assert len(blocks) >= 1, "Missing aws_s3_bucket 'input' resource."
        assert _has_nested_block(blocks[0]["body"], "cors_rule"), (
            "No cors_rule block found in input bucket.\n"
            "Add a cors_rule with allowed_headers=['*'], "
            "allowed_methods=['PUT', 'POST'], "
            "allowed_origins=[var.dashboard_origin], "
            "expose_headers=['ETag']."
        )

    def test_cors_allows_put_and_post(self) -> None:
        """CORS allowed_methods must include PUT and POST."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_s3_bucket", "input")
        assert len(blocks) >= 1, "Missing aws_s3_bucket 'input' resource."
        # Check for aws_s3_bucket_cors_policy resource if separate
        cors_blocks = _find_resource_blocks(source, "aws_s3_bucket_cors_policy", "input_cors")
        if cors_blocks:
            methods = _get_list_attr(cors_blocks[0]["body"], "allowed_methods") or []
        else:
            methods = _get_list_attr(blocks[0]["body"], "allowed_methods") or []
        assert "PUT" in methods, "CORS must allow PUT method for uploads"
        assert "POST" in methods, "CORS must allow POST method for uploads"

    def test_versioning_enabled(self) -> None:
        """Input bucket should have versioning enabled for data integrity."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_s3_bucket", "input")
        assert len(blocks) >= 1, "Missing aws_s3_bucket 'input' resource."
        versioning_blocks = _find_resource_blocks(source, "aws_s3_bucket_versioning", "input_versioning")
        if versioning_blocks:
            status = _get_attr(versioning_blocks[0]["body"], "status") or ""
        else:
            status = _get_attr(blocks[0]["body"], "status") or ""
        assert "Enabled" in status, (
            "Bucket versioning must be enabled (status = 'Enabled').\n"
            "Add aws_s3_bucket_versioning resource or versioning block."
        )

    def test_encryption_enabled(self) -> None:
        """Input bucket must have default SSE-S3 or SSE-KMS encryption."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_s3_bucket", "input")
        assert len(blocks) >= 1, "Missing aws_s3_bucket 'input' resource."
        enc_blocks = _find_resource_blocks(source, "aws_s3_bucket_server_side_encryption_configuration", "input_encryption")
        if enc_blocks:
            rule_has_sse = _has_nested_block(enc_blocks[0]["body"], "rule", "sse_algorithm")
        else:
            rule_has_sse = _has_nested_block(blocks[0]["body"], "rule", "sse_algorithm")
        assert rule_has_sse, (
            "Bucket must have server_side_encryption_configuration with "
            "sse_algorithm = 'AES256' or 'aws:kms'."
        )

    def test_tags_include_project(self) -> None:
        """Bucket tags must include a Project tag for cost allocation."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_s3_bucket", "input")
        assert len(blocks) >= 1, "Missing aws_s3_bucket 'input' resource."
        tags = _get_map_attr(blocks[0]["body"], "tags") or {}
        assert "Project" in tags, "Tags must include 'Project' for cost allocation"
        assert tags.get("Project", "") in ("ProjectCerberus", "project-cerberus"), (
            f"Project tag value incorrect: {tags.get('Project')}"
        )


# ══════════════════════════════════════════════
# Module: S3 Output Bucket
# ══════════════════════════════════════════════

@pytest.mark.integration
class TestS3OutputBucket:
    """S3 output bucket — worker writes detection results."""

    MODULE_PATH = "modules/s3-output/main.tf"

    def test_module_file_exists(self) -> None:
        """The s3-output module main.tf must exist."""
        assert _resource_exists(self.MODULE_PATH), (
            f"Missing: {TERRAFORM_ROOT / self.MODULE_PATH}\n"
            "Define an S3 bucket for worker result output."
        )

    def test_bucket_resource_defined(self) -> None:
        """Must define an aws_s3_bucket resource."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_s3_bucket", "output")
        assert len(blocks) >= 1, (
            'No aws_s3_bucket "output" resource found.\n'
            'Expected: resource "aws_s3_bucket" "output" { ... }'
        )

    def test_output_bucket_not_public(self) -> None:
        """Output bucket must NOT be publicly accessible."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_s3_bucket", "output")
        assert len(blocks) >= 1, "Missing aws_s3_bucket 'output' resource."
        acl = _get_attr(blocks[0]["body"], "acl")
        assert acl is None or "private" in acl.lower(), (
            f"Output bucket ACL must be 'private' or unset (default private), got: {acl}"
        )

    def test_encryption_enabled(self) -> None:
        """Output bucket must have server-side encryption."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_s3_bucket", "output")
        assert len(blocks) >= 1, "Missing aws_s3_bucket 'output' resource."
        enc_blocks = _find_resource_blocks(
            source, "aws_s3_bucket_server_side_encryption_configuration", "output_encryption"
        )
        if enc_blocks:
            rule_has_sse = _has_nested_block(enc_blocks[0]["body"], "rule", "sse_algorithm")
        else:
            rule_has_sse = _has_nested_block(blocks[0]["body"], "rule", "sse_algorithm")
        assert rule_has_sse, (
            "Output bucket must have server_side_encryption_configuration."
        )


# ══════════════════════════════════════════════
# Module: SQS Queue + DLQ
# ══════════════════════════════════════════════

@pytest.mark.integration
class TestSQSQueue:
    """SQS standard queue with DLQ attached."""

    MODULE_PATH = "modules/sqs/main.tf"

    def test_module_file_exists(self) -> None:
        """The sqs module main.tf must exist."""
        assert _resource_exists(self.MODULE_PATH), (
            f"Missing: {TERRAFORM_ROOT / self.MODULE_PATH}\n"
            "Define the SQS queue and DLQ resources."
        )

    def test_dlq_resource_exists(self) -> None:
        """A DLQ (dead-letter queue) must be defined."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_sqs_queue", "dlq")
        assert len(blocks) >= 1, (
            'No aws_sqs_queue "dlq" resource found.\n'
            'Expected: resource "aws_sqs_queue" "dlq" { ... }'
        )

    def test_main_queue_resource_exists(self) -> None:
        """The main SQS queue resource must be defined."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_sqs_queue", "jobs")
        assert len(blocks) >= 1, (
            'No aws_sqs_queue "jobs" resource found.\n'
            'Expected: resource "aws_sqs_queue" "jobs" { ... }'
        )

    def test_dlq_redrive_policy_attached(self) -> None:
        """Main queue must have redrive_policy pointing to the DLQ."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_sqs_queue", "jobs")
        assert len(blocks) >= 1, "Missing aws_sqs_queue 'jobs' resource."
        body = blocks[0]["body"]
        has_redrive = "redrive_policy" in body or "redrive_policy" in source
        assert has_redrive, (
            "Main queue must have a redrive_policy referencing the DLQ.\n"
            "redrive_policy = jsonencode({ deadLetterTargetArn = aws_sqs_queue.dlq.arn, maxReceiveCount = 3 })"
        )

    def test_visibility_timeout_set(self) -> None:
        """Visibility timeout must be set (default 30s, expect >= 300s for video processing)."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_sqs_queue", "jobs")
        assert len(blocks) >= 1, "Missing aws_sqs_queue 'jobs' resource."
        timeout_str = _get_attr(blocks[0]["body"], "visibility_timeout_seconds")
        if timeout_str is None:
            # Default is 30 — we expect an explicit value for video processing
            pytest.fail(
                "visibility_timeout_seconds not set. Set it to at least 300 "
                "(5 min) to cover max expected job duration."
            )
        timeout = int(timeout_str)
        assert timeout >= 300, (
            f"visibility_timeout_seconds should be >= 300 for video jobs, got {timeout}"
        )

    def test_queue_type_is_standard(self) -> None:
        """Queue should be a standard queue (not FIFO) for job processing."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_sqs_queue", "jobs")
        assert len(blocks) >= 1, "Missing aws_sqs_queue 'jobs' resource."
        fifo = _get_attr(blocks[0]["body"], "fifo_queue")
        if fifo is not None:
            assert fifo.lower() == "false", "Queue should be standard (not FIFO)"

    def test_max_receive_count_reasonable(self) -> None:
        """DLQ maxReceiveCount should be set (typically 3-5)."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_sqs_queue", "jobs")
        assert len(blocks) >= 1, "Missing aws_sqs_queue 'jobs' resource."
        body = blocks[0]["body"]
        # Extract maxReceiveCount from redrive_policy JSON
        m = re.search(r'maxReceiveCount\s*[:=]\s*(\d+)', body)
        if m:
            count = int(m.group(1))
            assert 1 <= count <= 10, (
                f"maxReceiveCount should be between 1 and 10, got {count}"
            )


# ══════════════════════════════════════════════
# Module: DynamoDB Table
# ══════════════════════════════════════════════

@pytest.mark.integration
class TestDynamoDBTable:
    """DynamoDB table — job metadata storage."""

    MODULE_PATH = "modules/dynamodb/main.tf"

    def test_module_file_exists(self) -> None:
        """The dynamodb module main.tf must exist."""
        assert _resource_exists(self.MODULE_PATH), (
            f"Missing: {TERRAFORM_ROOT / self.MODULE_PATH}\n"
            "Define the DynamoDB table resource."
        )

    def test_table_resource_exists(self) -> None:
        """Must define an aws_dynamodb_table resource."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_dynamodb_table", "jobs")
        assert len(blocks) >= 1, (
            'No aws_dynamodb_table "jobs" resource found.\n'
            'Expected: resource "aws_dynamodb_table" "jobs" { ... }'
        )

    def test_partition_key_is_job_id(self) -> None:
        """Partition key must be 'jobId' (string)."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_dynamodb_table", "jobs")
        assert len(blocks) >= 1, "Missing aws_dynamodb_table 'jobs' resource."
        body = blocks[0]["body"]
        # Check attribute definition
        attr_match = re.search(
            r'attribute\s*\{\s*name\s*=\s*"jobId"\s*type\s*=\s*"S"\s*\}', body, re.DOTALL
        )
        assert attr_match, (
            'Missing attribute definition: attribute { name = "jobId" type = "S" }'
        )
        # Check hash_key
        hash_key = _get_attr(body, "hash_key")
        assert hash_key == "jobId", (
            f"hash_key must be 'jobId', got: {hash_key}"
        )

    def test_ttl_enabled(self) -> None:
        """TTL must be enabled for auto-cleanup of expired job records."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_dynamodb_table", "jobs")
        assert len(blocks) >= 1, "Missing aws_dynamodb_table 'jobs' resource."
        body = blocks[0]["body"]
        has_ttl = "ttl" in body and ("attribute_name" in body or "enabled" in body)
        # Also check for aws_dynamodb_table_time_to_live resource
        ttl_resource = _find_resource_blocks(source, "aws_dynamodb_table_time_to_live", "jobs_ttl")
        if ttl_resource:
            has_ttl = True
        assert has_ttl, (
            "Table must have TTL enabled for auto-cleanup of expired items.\n"
            'Add ttl { attribute_name = "ttl" enabled = true }'
            'or aws_dynamodb_table_time_to_live resource.'
        )

    def test_ttl_attribute_name(self) -> None:
        """TTL attribute should be named 'ttl' for consistency."""
        source = _read_tf_file(self.MODULE_PATH)
        # Check inline ttl block
        table_blocks = _find_resource_blocks(source, "aws_dynamodb_table", "jobs")
        if table_blocks:
            ttl_attr = _get_attr(table_blocks[0]["body"], "attribute_name")
            if ttl_attr is not None:
                assert ttl_attr == "ttl", (
                    f"TTL attribute_name should be 'ttl', got: {ttl_attr}"
                )
                return
        # Check separate resource
        ttl_blocks = _find_resource_blocks(source, "aws_dynamodb_table_time_to_live", "jobs_ttl")
        if ttl_blocks:
            ttl_attr = _get_attr(ttl_blocks[0]["body"], "attribute_name")
            assert ttl_attr == "ttl", (
                f"TTL attribute_name should be 'ttl', got: {ttl_attr}"
            )
            return
        pytest.fail("No TTL configuration found.")

    def test_billing_mode_pay_per_request(self) -> None:
        """Billing mode must be PAY_PER_REQUEST (on-demand)."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_dynamodb_table", "jobs")
        assert len(blocks) >= 1, "Missing aws_dynamodb_table 'jobs' resource."
        billing = _get_attr(blocks[0]["body"], "billing_mode")
        assert billing is not None, "billing_mode must be set"
        assert "PAY_PER_REQUEST" in billing.upper(), (
            f"billing_mode must be 'PAY_PER_REQUEST', got: {billing}"
        )

    def test_tags_include_project(self) -> None:
        """Table tags must include Project tag."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_dynamodb_table", "jobs")
        assert len(blocks) >= 1, "Missing aws_dynamodb_table 'jobs' resource."
        tags = _get_map_attr(blocks[0]["body"], "tags") or {}
        assert "Project" in tags, "Tags must include 'Project'"


# ══════════════════════════════════════════════
# Module: IAM Roles & Policies
# ══════════════════════════════════════════════

@pytest.mark.integration
class TestIAMRoles:
    """IAM roles with least-privilege permissions."""

    MODULE_PATH = "modules/iam/main.tf"

    def test_module_file_exists(self) -> None:
        """The iam module main.tf must exist."""
        assert _resource_exists(self.MODULE_PATH), (
            f"Missing: {TERRAFORM_ROOT / self.MODULE_PATH}\n"
            "Define IAM roles and policies."
        )

    def test_worker_role_exists(self) -> None:
        """A worker IAM role must be defined."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_iam_role", "worker")
        assert len(blocks) >= 1, (
            'No aws_iam_role "worker" resource found.\n'
            'Expected: resource "aws_iam_role" "worker" { ... }'
        )

    def test_frontend_role_exists(self) -> None:
        """A frontend (dashboard) IAM role must be defined."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_iam_role", "frontend")
        assert len(blocks) >= 1, (
            'No aws_iam_role "frontend" resource found.\n'
            'Expected: resource "aws_iam_role" "frontend" { ... }'
        )

    def test_worker_role_assume_role_policy(self) -> None:
        """Worker role must trust the compute service (EC2, ECS, or Lambda)."""
        source = _read_tf_file(self.MODULE_PATH)
        blocks = _find_resource_blocks(source, "aws_iam_role", "worker")
        assert len(blocks) >= 1, "Missing aws_iam_role 'worker'."
        body = blocks[0]["body"]
        assume_policy = _extract_policy_document(body) or body
        has_service = any(
            s in assume_policy
            for s in ("ec2.amazonaws.com", "ecs-tasks.amazonaws.com", "lambda.amazonaws.com")
        )
        assert has_service, (
            "Worker role assume_role_policy must trust at least one compute service "
            "(ec2, ecs-tasks, or lambda)."
        )

    def test_worker_can_read_input_bucket(self) -> None:
        """Worker policy must allow s3:GetObject on the input bucket."""
        source = _read_tf_file(self.MODULE_PATH)
        # Search for a policy attachment or inline policy for worker
        policy_blocks = _find_resource_blocks(source, "aws_iam_role_policy", "worker_main")
        if not policy_blocks:
            policy_blocks = _find_resource_blocks(source, "aws_iam_policy", "worker_main")
        if not policy_blocks:
            policy_blocks = _find_resource_blocks(source, "aws_iam_role_policy_attachment", "worker_main")
        # Fallback: check for inline policy in the role itself
        worker_blocks = _find_resource_blocks(source, "aws_iam_role", "worker")
        if not policy_blocks and worker_blocks:
            policy_doc = _extract_policy_document(worker_blocks[0]["body"])
            if policy_doc:
                parsed = _resolve_hcl_json(worker_blocks[0]["body"])
                if parsed:
                    _assert_policy_statement(parsed, "s3:GetObject", "input")
                    return
        # Check standalone policies
        for pol in policy_blocks:
            pol_body = pol["body"]
            parsed = _resolve_hcl_json(pol_body)
            if parsed is None:
                pol_doc = _extract_policy_document(pol_body)
                if pol_doc and pol_doc.startswith("{"):
                    try:
                        parsed = json.loads(pol_doc)
                    except json.JSONDecodeError:
                        parsed = None
            if parsed:
                try:
                    _assert_policy_statement(parsed, "s3:GetObject", "input")
                    return
                except AssertionError:
                    continue
        pytest.fail(
            "No worker policy found that allows s3:GetObject on the input bucket."
        )

    def test_worker_can_write_output_bucket(self) -> None:
        """Worker policy must allow s3:PutObject on the output bucket."""
        source = _read_tf_file(self.MODULE_PATH)
        policy_blocks = _find_resource_blocks(source, "aws_iam_role_policy", "worker_main")
        if not policy_blocks:
            policy_blocks = _find_resource_blocks(source, "aws_iam_policy", "worker_main")
        for pol in policy_blocks:
            parsed = _resolve_hcl_json(pol["body"])
            if parsed:
                try:
                    _assert_policy_statement(parsed, "s3:PutObject", "output")
                    return
                except AssertionError:
                    continue
        pytest.fail(
            "No worker policy found that allows s3:PutObject on the output bucket."
        )

    def test_worker_can_read_sqs(self) -> None:
        """Worker policy must allow sqs:ReceiveMessage, sqs:DeleteMessage, sqs:ChangeMessageVisibility."""
        source = _read_tf_file(self.MODULE_PATH)
        policy_blocks = _find_resource_blocks(source, "aws_iam_role_policy", "worker_main")
        if not policy_blocks:
            policy_blocks = _find_resource_blocks(source, "aws_iam_policy", "worker_main")
        for pol in policy_blocks:
            parsed = _resolve_hcl_json(pol["body"])
            if parsed:
                try:
                    _assert_policy_statement(parsed, "sqs:ReceiveMessage", "sqs")
                    return
                except AssertionError:
                    continue
        pytest.fail(
            "No worker policy found with SQS permissions."
        )

    def test_worker_can_update_dynamodb(self) -> None:
        """Worker policy must allow dynamodb:PutItem and UpdateItem on the jobs table."""
        source = _read_tf_file(self.MODULE_PATH)
        policy_blocks = _find_resource_blocks(source, "aws_iam_role_policy", "worker_main")
        if not policy_blocks:
            policy_blocks = _find_resource_blocks(source, "aws_iam_policy", "worker_main")
        for pol in policy_blocks:
            parsed = _resolve_hcl_json(pol["body"])
            if parsed:
                try:
                    _assert_policy_statement(parsed, "dynamodb:PutItem", "dynamodb")
                    return
                except AssertionError:
                    continue
        pytest.fail(
            "No worker policy found with DynamoDB write permissions."
        )

    def test_frontend_can_write_sqs(self) -> None:
        """Frontend role must allow sqs:SendMessage on the job queue."""
        source = _read_tf_file(self.MODULE_PATH)
        policy_blocks = _find_resource_blocks(source, "aws_iam_role_policy", "frontend_main")
        if not policy_blocks:
            policy_blocks = _find_resource_blocks(source, "aws_iam_policy", "frontend_main")
        for pol in policy_blocks:
            parsed = _resolve_hcl_json(pol["body"])
            if parsed:
                try:
                    _assert_policy_statement(parsed, "sqs:SendMessage", "sqs")
                    return
                except AssertionError:
                    continue
        pytest.fail(
            "No frontend policy found with sqs:SendMessage permission."
        )

    def test_frontend_can_read_dynamodb(self) -> None:
        """Frontend role must allow dynamodb:Query and GetItem on the jobs table."""
        source = _read_tf_file(self.MODULE_PATH)
        policy_blocks = _find_resource_blocks(source, "aws_iam_role_policy", "frontend_main")
        if not policy_blocks:
            policy_blocks = _find_resource_blocks(source, "aws_iam_policy", "frontend_main")
        for pol in policy_blocks:
            parsed = _resolve_hcl_json(pol["body"])
            if parsed:
                try:
                    _assert_policy_statement(parsed, "dynamodb:Query", "dynamodb")
                    return
                except AssertionError:
                    continue
        pytest.fail(
            "No frontend policy found with DynamoDB read permissions."
        )

    def test_no_admin_policy(self) -> None:
        """No IAM policy should use 'Action': '*' or 'Resource': '*' (least-privilege)."""
        source = _read_tf_file(self.MODULE_PATH)
        all_policy_blocks = (
            _find_resource_blocks(source, "aws_iam_role_policy", "worker_main")
            + _find_resource_blocks(source, "aws_iam_role_policy", "frontend_main")
            + _find_resource_blocks(source, "aws_iam_policy", "worker_main")
            + _find_resource_blocks(source, "aws_iam_policy", "frontend_main")
        )
        for pol in all_policy_blocks:
            parsed = _resolve_hcl_json(pol["body"])
            if parsed:
                statements = parsed.get("Statement", [])
                for stmt in statements:
                    actions = stmt.get("Action", [])
                    if isinstance(actions, str):
                        actions = [actions]
                    for a in actions:
                        assert a != "*", (
                            f"Wildcard Action '*' found in policy. "
                            f"Least-privilege requires scoped actions."
                        )
                    resources = stmt.get("Resource", [])
                    if isinstance(resources, str):
                        resources = [resources]
                    for r in resources:
                        assert r != "*", (
                            f"Wildcard Resource '*' found in policy. "
                            f"Least-privilege requires resource-scoped ARNs."
                        )


# ══════════════════════════════════════════════
# Root Terraform Configuration
# ══════════════════════════════════════════════

@pytest.mark.integration
class TestTerraformRoot:
    """Root main.tf — module wiring and outputs."""

    MAIN_PATH = "main.tf"
    OUTPUTS_PATH = "outputs.tf"

    def test_main_tf_exists(self) -> None:
        """Root main.tf must exist."""
        assert _resource_exists(self.MAIN_PATH), (
            f"Missing: {TERRAFORM_ROOT / self.MAIN_PATH}\n"
            "Root Terraform configuration file required."
        )

    def test_outputs_tf_exists(self) -> None:
        """Root outputs.tf must exist."""
        assert _resource_exists(self.OUTPUTS_PATH), (
            f"Missing: {TERRAFORM_ROOT / self.OUTPUTS_PATH}\n"
            "Define Terraform outputs for all created resources."
        )

    def test_output_input_bucket_id(self) -> None:
        """Output 'input_bucket_id' must be defined."""
        source = _read_tf_file(self.OUTPUTS_PATH)
        blocks = _find_output_blocks(source, "input_bucket_id")
        assert len(blocks) >= 1, (
            'Missing output "input_bucket_id" — needed by frontend for uploads.'
        )

    def test_output_input_bucket_arn(self) -> None:
        """Output 'input_bucket_arn' must be defined."""
        source = _read_tf_file(self.OUTPUTS_PATH)
        blocks = _find_output_blocks(source, "input_bucket_arn")
        assert len(blocks) >= 1, (
            'Missing output "input_bucket_arn" — needed by IAM policies.'
        )

    def test_output_output_bucket_id(self) -> None:
        """Output 'output_bucket_id' must be defined."""
        source = _read_tf_file(self.OUTPUTS_PATH)
        blocks = _find_output_blocks(source, "output_bucket_id")
        assert len(blocks) >= 1, 'Missing output "output_bucket_id".'

    def test_output_output_bucket_arn(self) -> None:
        """Output 'output_bucket_arn' must be defined."""
        source = _read_tf_file(self.OUTPUTS_PATH)
        blocks = _find_output_blocks(source, "output_bucket_arn")
        assert len(blocks) >= 1, 'Missing output "output_bucket_arn".'

    def test_output_job_queue_url(self) -> None:
        """Output 'job_queue_url' must be defined."""
        source = _read_tf_file(self.OUTPUTS_PATH)
        blocks = _find_output_blocks(source, "job_queue_url")
        assert len(blocks) >= 1, (
            'Missing output "job_queue_url" — needed by frontend to enqueue jobs.'
        )

    def test_output_job_queue_arn(self) -> None:
        """Output 'job_queue_arn' must be defined."""
        source = _read_tf_file(self.OUTPUTS_PATH)
        blocks = _find_output_blocks(source, "job_queue_arn")
        assert len(blocks) >= 1, 'Missing output "job_queue_arn".'

    def test_output_dlq_arn(self) -> None:
        """Output 'dlq_arn' must be defined."""
        source = _read_tf_file(self.OUTPUTS_PATH)
        blocks = _find_output_blocks(source, "dlq_arn")
        assert len(blocks) >= 1, 'Missing output "dlq_arn".'

    def test_output_jobs_table_name(self) -> None:
        """Output 'jobs_table_name' must be defined."""
        source = _read_tf_file(self.OUTPUTS_PATH)
        blocks = _find_output_blocks(source, "jobs_table_name")
        assert len(blocks) >= 1, (
            'Missing output "jobs_table_name" — needed by frontend and workers.'
        )

    def test_output_jobs_table_arn(self) -> None:
        """Output 'jobs_table_arn' must be defined."""
        source = _read_tf_file(self.OUTPUTS_PATH)
        blocks = _find_output_blocks(source, "jobs_table_arn")
        assert len(blocks) >= 1, 'Missing output "jobs_table_arn".'

    def test_output_worker_role_arn(self) -> None:
        """Output 'worker_role_arn' must be defined."""
        source = _read_tf_file(self.OUTPUTS_PATH)
        blocks = _find_output_blocks(source, "worker_role_arn")
        assert len(blocks) >= 1, 'Missing output "worker_role_arn".'

    def test_output_frontend_role_arn(self) -> None:
        """Output 'frontend_role_arn' must be defined."""
        source = _read_tf_file(self.OUTPUTS_PATH)
        blocks = _find_output_blocks(source, "frontend_role_arn")
        assert len(blocks) >= 1, 'Missing output "frontend_role_arn".'


# ══════════════════════════════════════════════
# Module Wiring (root main.tf)
# ══════════════════════════════════════════════

@pytest.mark.integration
class TestModuleWiring:
    """Root main.tf must wire all modules together."""

    MAIN_PATH = "main.tf"

    def test_s3_input_module_wired(self) -> None:
        """Root main.tf must reference the s3-input module."""
        source = _read_tf_file(self.MAIN_PATH)
        blocks = _find_module_blocks(source, "input_bucket")
        # Could also be named differently; check for s3-input source
        has_input = any("s3-input" in b["body"] or "input" in b["name"].lower() for b in blocks)
        has_input = has_input or "s3-input" in source
        assert has_input, (
            "Root main.tf must include a module referencing s3-input.\n"
            'Expected: module "input_bucket" { source = "./modules/s3-input" ... }'
        )

    def test_s3_output_module_wired(self) -> None:
        """Root main.tf must reference the s3-output module."""
        source = _read_tf_file(self.MAIN_PATH)
        has_output = "s3-output" in source or "output_bucket" in source
        assert has_output, (
            "Root main.tf must include a module referencing s3-output."
        )

    def test_sqs_module_wired(self) -> None:
        """Root main.tf must reference the sqs module."""
        source = _read_tf_file(self.MAIN_PATH)
        has_sqs = '"sqs"' in source or './modules/sqs"' in source or 'module "job_queue"' in source
        assert has_sqs, (
            "Root main.tf must include a module referencing sqs."
        )

    def test_dynamodb_module_wired(self) -> None:
        """Root main.tf must reference the dynamodb module."""
        source = _read_tf_file(self.MAIN_PATH)
        has_ddb = "dynamodb" in source or "dynamo" in source
        assert has_ddb, (
            "Root main.tf must include a module referencing dynamodb."
        )

    def test_iam_module_wired(self) -> None:
        """Root main.tf must reference the iam module."""
        source = _read_tf_file(self.MAIN_PATH)
        has_iam = '"iam"' in source or './modules/iam"' in source
        assert has_iam, (
            "Root main.tf must include a module referencing iam."
        )

    def test_variables_tf_exists(self) -> None:
        """Root variables.tf must exist."""
        assert _resource_exists("variables.tf"), (
            f"Missing: {TERRAFORM_ROOT / 'variables.tf'}\n"
            "Define input variables for environment, project name, etc."
        )

    def test_required_variables_defined(self) -> None:
        """Must define variables for environment, project_name, and dashboard_origin."""
        source = _read_tf_file("variables.tf")
        for var_name in ("environment", "project_name", "dashboard_origin"):
            assert f'variable "{var_name}"' in source, (
                f'Missing variable "{var_name}" in variables.tf.\n'
                f"Required for resource naming and CORS configuration."
            )
