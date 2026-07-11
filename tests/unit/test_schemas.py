"""LOCKED — Unit tests for Pydantic data schemas (Task 1.1).

Tests JobInput, JobResult, and Detection models: field types, defaults,
validation, and serialization. Do NOT modify these tests.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import get_args, Literal

import pytest
from pydantic import ValidationError

from worker.src.schemas import Detection, JobInput, JobResult


# ──────────────────────────────────────────────
# Detection
# ──────────────────────────────────────────────

class TestDetection:
    """Detection model — YOLO format bbox."""

    def test_fields(self) -> None:
        """All fields have correct types."""
        det = Detection(
            class_id=0,
            class_name="person",
            confidence=0.95,
            bbox=(0.5, 0.5, 0.2, 0.3),
        )
        assert det.class_id == 0
        assert isinstance(det.class_id, int)
        assert det.class_name == "person"
        assert isinstance(det.class_name, str)
        assert det.confidence == 0.95
        assert isinstance(det.confidence, float)
        assert det.bbox == (0.5, 0.5, 0.2, 0.3)
        assert isinstance(det.bbox, tuple)
        assert len(det.bbox) == 4
        for v in det.bbox:
            assert isinstance(v, float)

    def test_bbox_normalized_range(self) -> None:
        """bbox values are normalized 0-1 (YOLO format)."""
        det = Detection(class_id=1, class_name="car", confidence=0.5, bbox=(0.0, 0.0, 1.0, 1.0))
        assert det.bbox == (0.0, 0.0, 1.0, 1.0)

    @pytest.mark.parametrize(
        "invalid_bbox",
        [
            (1.5, 0.5, 0.2, 0.3),  # x_center > 1
            (-0.1, 0.5, 0.2, 0.3),  # negative
            (0.5, 1.5, 0.2, 0.3),  # y_center > 1
            (0.5, 0.5, 0.0, 0.3),  # zero width (allowable? no detection area)
            (0.5, 0.5, -0.1, 0.3),  # negative width
        ],
    )
    def test_bbox_out_of_range(self, invalid_bbox: tuple) -> None:
        """Out-of-range bbox values should be rejected or handled."""
        if all(v == 0 for v in invalid_bbox):
            pytest.skip("zero bbox may be valid")
        with pytest.raises(ValidationError):
            Detection(
                class_id=0,
                class_name="obj",
                confidence=0.5,
                bbox=invalid_bbox,
            )

    def test_confidence_bounds(self) -> None:
        """Confidence is float in [0.0, 1.0]."""
        det = Detection(class_id=0, class_name="obj", confidence=0.0, bbox=(0.5,) * 4)
        assert det.confidence == 0.0
        det = Detection(class_id=0, class_name="obj", confidence=1.0, bbox=(0.5,) * 4)
        assert det.confidence == 1.0
        with pytest.raises(ValidationError):
            Detection(class_id=0, class_name="obj", confidence=-0.01, bbox=(0.5,) * 4)
        with pytest.raises(ValidationError):
            Detection(class_id=0, class_name="obj", confidence=1.01, bbox=(0.5,) * 4)

    def test_serialization_json(self) -> None:
        """Detection round-trips through JSON."""
        det = Detection(class_id=2, class_name="dog", confidence=0.88, bbox=(0.3, 0.4, 0.1, 0.2))
        raw = det.model_dump_json()
        restored = Detection.model_validate_json(raw)
        assert restored == det

    def test_serialization_dict(self) -> None:
        """Detection round-trips through dict."""
        det = Detection(class_id=3, class_name="cat", confidence=0.75, bbox=(0.5, 0.5, 0.3, 0.3))
        raw = det.model_dump()
        restored = Detection.model_validate(raw)
        assert restored == det


# ──────────────────────────────────────────────
# JobInput
# ──────────────────────────────────────────────

class TestJobInput:
    """JobInput model — job metadata."""

    def test_fields(self) -> None:
        """All fields present with correct types."""
        inp = JobInput(
            job_id="job-001",
            video_s3_key="videos/test.mp4",
            input_bucket="my-bucket",
        )
        assert inp.job_id == "job-001"
        assert isinstance(inp.job_id, str)
        assert inp.video_s3_key == "videos/test.mp4"
        assert isinstance(inp.video_s3_key, str)
        assert inp.input_bucket == "my-bucket"
        assert isinstance(inp.input_bucket, str)

    def test_frame_step_default(self) -> None:
        """frame_step defaults to 1."""
        inp = JobInput(job_id="j1", video_s3_key="v.mp4", input_bucket="b")
        assert inp.frame_step == 1
        assert isinstance(inp.frame_step, int)

    def test_frame_step_custom(self) -> None:
        """frame_step can be overridden."""
        inp = JobInput(job_id="j1", video_s3_key="v.mp4", input_bucket="b", frame_step=5)
        assert inp.frame_step == 5

    @pytest.mark.parametrize("bad_step", [0, -1, -100])
    def test_frame_step_must_be_positive(self, bad_step: int) -> None:
        """frame_step must be a positive integer."""
        with pytest.raises(ValidationError):
            JobInput(job_id="j1", video_s3_key="v.mp4", input_bucket="b", frame_step=bad_step)

    def test_serialization(self) -> None:
        """JobInput round-trips through JSON."""
        inp = JobInput(job_id="j2", video_s3_key="vids/clip.mp4", input_bucket="bucket-a", frame_step=3)
        raw = inp.model_dump_json()
        restored = JobInput.model_validate_json(raw)
        assert restored == inp

    def test_empty_strings(self) -> None:
        """Empty string fields are still valid (storage constraints separate)."""
        inp = JobInput(job_id="", video_s3_key="", input_bucket="")
        assert inp.job_id == ""
        assert inp.video_s3_key == ""
        assert inp.input_bucket == ""


# ──────────────────────────────────────────────
# JobResult
# ──────────────────────────────────────────────

class TestJobResult:
    """JobResult model — processing output."""

    @pytest.fixture
    def sample_job_input(self) -> JobInput:
        return JobInput(job_id="job-999", video_s3_key="v.mp4", input_bucket="in-bucket")

    def test_fields(self, sample_job_input: JobInput) -> None:
        """All fields present with correct types."""
        now = datetime.now(timezone.utc)
        result = JobResult(
            job_id="job-999",
            status="completed",
            frames_processed=42,
            detections=[],
            output_s3_key="results/job-999.json",
            worker_type="test",
            started_at=now,
        )
        assert result.job_id == "job-999"
        assert isinstance(result.job_id, str)
        assert result.status == "completed"
        assert result.frames_processed == 42
        assert isinstance(result.frames_processed, int)
        assert result.detections == []
        assert isinstance(result.detections, list)
        assert result.output_s3_key == "results/job-999.json"
        assert isinstance(result.output_s3_key, str)
        assert result.worker_type == "test"
        assert isinstance(result.worker_type, str)
        assert isinstance(result.started_at, datetime)

    def test_status_literal(self) -> None:
        """status accepts only 'completed' or 'failed'."""
        now = datetime.now(timezone.utc)
        JobResult(
            job_id="j1", status="completed", frames_processed=0, detections=[],
            output_s3_key="k", worker_type="w", started_at=now,
        )
        JobResult(
            job_id="j1", status="failed", frames_processed=0, detections=[],
            output_s3_key="k", worker_type="w", started_at=now,
        )
        with pytest.raises(ValidationError):
            JobResult(
                job_id="j1", status="running", frames_processed=0, detections=[],
                output_s3_key="k", worker_type="w", started_at=now,
            )

    def test_optional_fields_default_none(self) -> None:
        """completed_at and error_message default to None."""
        now = datetime.now(timezone.utc)
        result = JobResult(
            job_id="j1", status="completed", frames_processed=0, detections=[],
            output_s3_key="k", worker_type="w", started_at=now,
        )
        assert result.completed_at is None
        assert result.error_message is None

    def test_optional_fields_can_be_set(self) -> None:
        """Optional fields accept values."""
        now = datetime.now(timezone.utc)
        later = datetime.now(timezone.utc)
        result = JobResult(
            job_id="j1", status="failed", frames_processed=10, detections=[],
            output_s3_key="k", worker_type="w", started_at=now,
            completed_at=later, error_message="Model crashed",
        )
        assert result.completed_at == later
        assert result.error_message == "Model crashed"

    def test_detections_with_nested_objects(self) -> None:
        """detections list holds (frame_index, List[Detection]) tuples."""
        now = datetime.now(timezone.utc)
        dets = [
            Detection(class_id=0, class_name="person", confidence=0.95, bbox=(0.5, 0.5, 0.2, 0.3)),
        ]
        result = JobResult(
            job_id="j1", status="completed", frames_processed=1,
            detections=[(0, dets)],
            output_s3_key="k", worker_type="w", started_at=now,
        )
        assert len(result.detections) == 1
        frame_idx, frame_dets = result.detections[0]
        assert frame_idx == 0
        assert len(frame_dets) == 1
        assert isinstance(frame_dets[0], Detection)

    def test_serialization(self) -> None:
        """JobResult round-trips through JSON with nested Detection objects."""
        now = datetime.now(timezone.utc)
        dets = [Detection(class_id=1, class_name="car", confidence=0.8, bbox=(0.2, 0.3, 0.4, 0.5))]
        result = JobResult(
            job_id="j1", status="completed", frames_processed=5,
            detections=[(0, dets)],
            output_s3_key="out/j1.json", worker_type="ec2",
            started_at=now,
        )
        raw = result.model_dump_json()
        restored = JobResult.model_validate_json(raw)
        assert restored.job_id == result.job_id
        assert restored.status == result.status
        assert restored.frames_processed == result.frames_processed
        assert len(restored.detections) == len(result.detections)
        for (rf, rd), (of, od) in zip(restored.detections, result.detections):
            assert rf == of
            assert rd == od
        assert restored.worker_type == result.worker_type

    def test_failed_status_without_error_message(self) -> None:
        """A 'failed' status is valid even without an error_message."""
        now = datetime.now(timezone.utc)
        result = JobResult(
            job_id="j1", status="failed", frames_processed=5, detections=[],
            output_s3_key="k", worker_type="w", started_at=now,
        )
        assert result.status == "failed"
        assert result.error_message is None
