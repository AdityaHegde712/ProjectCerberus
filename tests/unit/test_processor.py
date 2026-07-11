"""LOCKED — Unit tests for process_video() orchestrator (Task 1.7).

Tests with mocked storage adapter, mocked YOLO detector, and synthetic
video frames. Covers happy path, empty video, corrupt frames, and
no-detections edge cases. Do NOT modify these tests.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from worker.src.processor import process_video
from worker.src.schemas import Detection, JobInput, JobResult


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def make_rgb_frame(height: int = 480, width: int = 640) -> np.ndarray:
    """Create a synthetic RGB frame."""
    return np.zeros((height, width, 3), dtype=np.uint8)


def _make_test_video_bytes(num_frames: int = 3,
                           height: int = 480,
                           width: int = 640) -> bytes:
    """Build a minimal H.264 / raw video byte blob.

    Uses OpenCV to encode frames into a real video container so that the
    implementation can decode them back.
    """
    import cv2
    import tempfile
    fname = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            fname = tmp.name
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(fname, fourcc, 30.0, (width, height))
        for _ in range(num_frames):
            frame = make_rgb_frame(height, width)
            writer.write(frame)
        writer.release()
        with open(fname, "rb") as f:
            return f.read()
    finally:
        if fname is not None:
            import os
            try:
                os.unlink(fname)
            except OSError:
                pass


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture
def sample_job_input() -> JobInput:
    return JobInput(
        job_id="test-job-001",
        video_s3_key="videos/sample.mp4",
        input_bucket="my-input-bucket",
        frame_step=1,
    )


@pytest.fixture
def three_frame_video() -> bytes:
    """A real .mp4 video with 3 frames."""
    return _make_test_video_bytes(num_frames=3)


# ──────────────────────────────────────────────
# Happy path
# ──────────────────────────────────────────────

class TestProcessVideoHappyPath:
    """process_video() with valid input and mock components."""

    def test_returns_jobresult(self, sample_job_input: JobInput,
                               three_frame_video: bytes) -> None:
        """Returns a JobResult instance."""
        with (patch("worker.src.storage.read_video", return_value=three_frame_video),
              patch("worker.src.storage.write_json"),
              patch("worker.src.detector.predict", return_value=[])):
            result = process_video(sample_job_input)
        assert isinstance(result, JobResult)

    def test_job_id_matches_input(self, sample_job_input: JobInput,
                                  three_frame_video: bytes) -> None:
        """Returned JobResult.job_id matches the input."""
        with (patch("worker.src.storage.read_video", return_value=three_frame_video),
              patch("worker.src.storage.write_json"),
              patch("worker.src.detector.predict", return_value=[])):
            result = process_video(sample_job_input)
        assert result.job_id == sample_job_input.job_id

    def test_status_completed(self, sample_job_input: JobInput,
                              three_frame_video: bytes) -> None:
        """Status is 'completed' when processing succeeds."""
        with (patch("worker.src.storage.read_video", return_value=three_frame_video),
              patch("worker.src.storage.write_json"),
              patch("worker.src.detector.predict", return_value=[])):
            result = process_video(sample_job_input)
        assert result.status == "completed"

    def test_frames_processed_count(self, sample_job_input: JobInput,
                                    three_frame_video: bytes) -> None:
        """frames_processed equals number of frames in video with step=1."""
        with (patch("worker.src.storage.read_video", return_value=three_frame_video),
              patch("worker.src.storage.write_json"),
              patch("worker.src.detector.predict", return_value=[])):
            result = process_video(sample_job_input)
        assert result.frames_processed == 3

    def test_detections_included(self, sample_job_input: JobInput,
                                 three_frame_video: bytes) -> None:
        """Detections from predict() appear in JobResult."""
        fake_dets = [
            Detection(class_id=0, class_name="person", confidence=0.95,
                      bbox=(0.5, 0.5, 0.2, 0.3)),
        ]
        with (patch("worker.src.storage.read_video", return_value=three_frame_video),
              patch("worker.src.storage.write_json"),
              patch("worker.src.detector.predict", return_value=fake_dets)):
            result = process_video(sample_job_input)

        assert len(result.detections) == 3
        for frame_idx, dets in result.detections:
            assert isinstance(frame_idx, int)
            assert len(dets) == 1
            assert dets[0] == fake_dets[0]

    def test_worker_type_set(self, sample_job_input: JobInput,
                             three_frame_video: bytes) -> None:
        """worker_type is a non-empty string."""
        with (patch("worker.src.storage.read_video", return_value=three_frame_video),
              patch("worker.src.storage.write_json"),
              patch("worker.src.detector.predict", return_value=[])):
            result = process_video(sample_job_input)
        assert isinstance(result.worker_type, str)
        assert len(result.worker_type) > 0

    def test_timestamps(self, sample_job_input: JobInput,
                        three_frame_video: bytes) -> None:
        """started_at and completed_at are set correctly."""
        with (patch("worker.src.storage.read_video", return_value=three_frame_video),
              patch("worker.src.storage.write_json"),
              patch("worker.src.detector.predict", return_value=[])):
            result = process_video(sample_job_input)

        assert isinstance(result.started_at, datetime)
        assert isinstance(result.completed_at, datetime)
        assert result.completed_at >= result.started_at

    def test_output_s3_key_populated(self, sample_job_input: JobInput,
                                     three_frame_video: bytes) -> None:
        """output_s3_key is a non-empty string."""
        with (patch("worker.src.storage.read_video", return_value=three_frame_video),
              patch("worker.src.storage.write_json"),
              patch("worker.src.detector.predict", return_value=[])):
            result = process_video(sample_job_input)
        assert isinstance(result.output_s3_key, str)
        assert len(result.output_s3_key) > 0


# ──────────────────────────────────────────────
# Storage interaction
# ──────────────────────────────────────────────

class TestProcessVideoStorage:
    """process_video() reads input and writes output via storage adapter."""

    def test_reads_video_from_storage(self, sample_job_input: JobInput) -> None:
        """Calls storage.read_video with the correct key."""
        mock_read = MagicMock(return_value=b"")
        with (patch("worker.src.storage.read_video", mock_read),
              patch("worker.src.storage.write_json"),
              patch("worker.src.detector.predict", return_value=[])):
            process_video(sample_job_input)
        mock_read.assert_called_once_with(sample_job_input.video_s3_key)

    def test_writes_results_to_storage(self, sample_job_input: JobInput,
                                       three_frame_video: bytes) -> None:
        """Calls storage.write_json with result data."""
        mock_write = MagicMock()
        with (patch("worker.src.storage.read_video", return_value=three_frame_video),
              patch("worker.src.storage.write_json", mock_write),
              patch("worker.src.detector.predict", return_value=[])):
            result = process_video(sample_job_input)

        mock_write.assert_called_once()
        key, data = mock_write.call_args[0]
        assert isinstance(key, str)
        assert data["job_id"] == sample_job_input.job_id
        assert data["status"] == "completed"


# ──────────────────────────────────────────────
# frame_step behavior
# ──────────────────────────────────────────────

class TestProcessVideoFrameStep:
    """process_video() respects the frame_step parameter."""

    @pytest.fixture
    def ten_frame_video(self) -> bytes:
        """A real .mp4 video with 10 frames."""
        return _make_test_video_bytes(num_frames=10)

    def test_step_1_processes_all_frames(self, sample_job_input: JobInput,
                                         ten_frame_video: bytes) -> None:
        """frame_step=1 processes every frame."""
        job = JobInput(job_id="s1", video_s3_key="v.mp4", input_bucket="b",
                       frame_step=1)
        with (patch("worker.src.storage.read_video", return_value=ten_frame_video),
              patch("worker.src.storage.write_json"),
              patch("worker.src.detector.predict", return_value=[])):
            result = process_video(job)
        assert result.frames_processed == 10

    def test_step_3_processes_every_third_frame(self, ten_frame_video: bytes) -> None:
        """frame_step=3 processes frames 0, 3, 6, 9 = 4 frames."""
        job = JobInput(job_id="s3", video_s3_key="v.mp4", input_bucket="b",
                       frame_step=3)
        with (patch("worker.src.storage.read_video", return_value=ten_frame_video),
              patch("worker.src.storage.write_json"),
              patch("worker.src.detector.predict", return_value=[])):
            result = process_video(job)
        # ceil(10 / 3) = 4
        assert result.frames_processed == 4

    def test_step_larger_than_video_length(self, ten_frame_video: bytes) -> None:
        """frame_step > video length processes only the first frame."""
        job = JobInput(job_id="big-step", video_s3_key="v.mp4", input_bucket="b",
                       frame_step=100)
        with (patch("worker.src.storage.read_video", return_value=ten_frame_video),
              patch("worker.src.storage.write_json"),
              patch("worker.src.detector.predict", return_value=[])):
            result = process_video(job)
        assert result.frames_processed == 1


# ──────────────────────────────────────────────
# Edge cases
# ──────────────────────────────────────────────

class TestProcessVideoEdgeCases:
    """process_video() handles edge cases gracefully."""

    def test_zero_byte_video(self) -> None:
        """Zero-byte video returns status=failed with error message."""
        job = JobInput(job_id="zero", video_s3_key="empty.mp4", input_bucket="b")
        with (patch("worker.src.storage.read_video", return_value=b""),
              patch("worker.src.storage.write_json"),
              patch("worker.src.detector.predict", return_value=[])):
            result = process_video(job)

        assert result.job_id == "zero"
        assert result.status == "failed"
        assert result.error_message is not None

    def test_no_detections(self) -> None:
        """Video with no objects returns completed with empty detections."""
        video = _make_test_video_bytes(num_frames=2)
        job = JobInput(job_id="nodets", video_s3_key="v.mp4", input_bucket="b")
        with (patch("worker.src.storage.read_video", return_value=video),
              patch("worker.src.storage.write_json"),
              patch("worker.src.detector.predict", return_value=[])):
            result = process_video(job)

        assert result.status == "completed"
        assert result.frames_processed == 2
        assert len(result.detections) == 2
        for _, dets in result.detections:
            assert len(dets) == 0

    def test_storage_read_failure(self, sample_job_input: JobInput) -> None:
        """Storage read failure returns status=failed."""
        with (patch("worker.src.storage.read_video",
                    side_effect=FileNotFoundError("Video not found")),
              patch("worker.src.storage.write_json")):
            result = process_video(sample_job_input)

        assert result.status == "failed"
        assert result.error_message is not None

    def test_detector_crashes_on_frame(self, sample_job_input: JobInput,
                                       three_frame_video: bytes) -> None:
        """If predict() crashes, status=failed with error."""
        mock_predict = MagicMock(side_effect=[
            [],
            RuntimeError("Detector crashed"),
        ])
        with (patch("worker.src.storage.read_video", return_value=three_frame_video),
              patch("worker.src.storage.write_json"),
              patch("worker.src.detector.predict", mock_predict)):
            result = process_video(sample_job_input)

        assert result.status == "failed"
        assert result.error_message is not None

    def test_storage_write_failure(self, sample_job_input: JobInput,
                                   three_frame_video: bytes) -> None:
        """Storage write failure still returns a valid JobResult."""
        with (patch("worker.src.storage.read_video", return_value=three_frame_video),
              patch("worker.src.storage.write_json",
                    side_effect=IOError("Write failed")),
              patch("worker.src.detector.predict", return_value=[])):
            result = process_video(sample_job_input)

        assert isinstance(result, JobResult)
        assert result.job_id == sample_job_input.job_id


# ──────────────────────────────────────────────
# Failed-status details
# ──────────────────────────────────────────────

class TestProcessVideoFailedStatus:
    """process_video() correctly builds failed JobResult."""

    def test_error_message_present(self, sample_job_input: JobInput) -> None:
        """Failed result includes a non-empty error_message."""
        with (patch("worker.src.storage.read_video",
                    side_effect=Exception("Unexpected error")),
              patch("worker.src.storage.write_json")):
            result = process_video(sample_job_input)

        assert result.status == "failed"
        assert isinstance(result.error_message, str)
        assert len(result.error_message) > 0

    def test_failed_can_have_completed_at(self, sample_job_input: JobInput) -> None:
        """A failed job may still set completed_at."""
        with (patch("worker.src.storage.read_video",
                    side_effect=Exception("err")),
              patch("worker.src.storage.write_json")):
            result = process_video(sample_job_input)

        assert result.status == "failed"
        # Error message is required
        assert result.error_message is not None
