"""LOCKED — Unit tests for S3 storage adapter (Task 1.5).

Tests read_video() and write_json() with local filesystem mock.
Do NOT modify these tests.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from worker.src.storage import read_video, write_json


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture
def temp_dir() -> str:
    """Provide a temporary directory for local file operations."""
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp


@pytest.fixture
def sample_video_bytes() -> bytes:
    """Return a small blob simulating raw video bytes."""
    return b"\x00\x01\x02\x03" * 256  # 1024 bytes of fake video


# ──────────────────────────────────────────────
# write_json
# ──────────────────────────────────────────────

class TestWriteJson:
    """write_json() writes a dictionary as JSON to storage."""

    def test_writes_to_local_file(self, temp_dir: str) -> None:
        """Write a JSON dict to a local file path."""
        key = Path(temp_dir, "test_output.json").as_posix()
        data = {"job_id": "job-001", "status": "completed"}
        write_json(key, data)
        assert Path(key).exists()
        with open(key, "r") as f:
            contents = json.load(f)
        assert contents == data

    def test_writes_nested_data(self, temp_dir: str) -> None:
        """Write nested dicts and lists correctly."""
        key = Path(temp_dir, "nested.json").as_posix()
        data = {
            "job_id": "j1",
            "frames": [
                {"index": 0, "detections": [{"class": "person", "conf": 0.9}]},
            ],
        }
        write_json(key, data)
        with open(key, "r") as f:
            contents = json.load(f)
        assert contents == data

    def test_overwrites_existing_file(self, temp_dir: str) -> None:
        """Write over an existing file replaces its contents."""
        key = Path(temp_dir, "overwrite.json").as_posix()
        write_json(key, {"first": "data"})
        write_json(key, {"second": "data"})
        with open(key, "r") as f:
            contents = json.load(f)
        assert contents == {"second": "data"}

    def test_empty_dict(self, temp_dir: str) -> None:
        """Write an empty dict produces valid '{}'."""
        key = Path(temp_dir, "empty.json").as_posix()
        write_json(key, {})
        with open(key, "r") as f:
            contents = json.load(f)
        assert contents == {}

    @pytest.mark.parametrize("invalid_data", [None, "string", 42, [1, 2, 3]])
    def test_invalid_data_type_raises(self, temp_dir: str, invalid_data: Any) -> None:
        """Non-dict data raises TypeError."""
        key = Path(temp_dir, "bad.json").as_posix()
        with pytest.raises(TypeError):
            write_json(key, invalid_data)


# ──────────────────────────────────────────────
# read_video
# ──────────────────────────────────────────────

class TestReadVideo:
    """read_video() reads raw video bytes from storage."""

    def test_reads_existing_file(self, temp_dir: str, sample_video_bytes: bytes) -> None:
        """Read back bytes that were previously written."""
        key = Path(temp_dir, "video.mp4").as_posix()
        with open(key, "wb") as f:
            f.write(sample_video_bytes)
        result = read_video(key)
        assert isinstance(result, bytes)
        assert result == sample_video_bytes

    def test_reads_large_file(self, temp_dir: str) -> None:
        """Read a large blob (10 MB) without issue."""
        key = Path(temp_dir, "large.mp4").as_posix()
        large_data = b"\xff" * (10 * 1024 * 1024)  # 10 MB
        with open(key, "wb") as f:
            f.write(large_data)
        result = read_video(key)
        assert len(result) == len(large_data)
        assert result == large_data

    def test_empty_file(self, temp_dir: str) -> None:
        """Read an empty file returns empty bytes."""
        key = Path(temp_dir, "empty.mp4").as_posix()
        Path(key).write_text("")
        result = read_video(key)
        assert result == b""

    def test_file_not_found_raises(self) -> None:
        """Reading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            read_video("/tmp/nonexistent_video_xyz.mp4")


# ──────────────────────────────────────────────
# Round-trip integration (local mode)
# ──────────────────────────────────────────────

class TestStorageRoundTrip:
    """read_video + write_json work together via local filesystem."""

    def test_write_then_read_video(self, temp_dir: str) -> None:
        """Write raw video bytes then read them back."""
        video_path = Path(temp_dir, "roundtrip.mp4").as_posix()
        original = b"fake video content here"
        with open(video_path, "wb") as f:
            f.write(original)
        result = read_video(video_path)
        assert result == original

    def test_write_then_read_json(self, temp_dir: str) -> None:
        """Write JSON results then read and parse them."""
        json_path = Path(temp_dir, "results.json").as_posix()
        data: Dict[str, Any] = {
            "job_id": "j-test",
            "status": "completed",
            "frames_processed": 10,
            "detections": [],
        }
        write_json(json_path, data)
        result = read_video(json_path)
        assert isinstance(result, bytes)
        parsed = json.loads(result.decode("utf-8"))
        assert parsed == data
