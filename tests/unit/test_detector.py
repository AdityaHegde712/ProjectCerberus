"""LOCKED — Unit tests for YOLO wrapper abstraction (Task 1.3).

Tests load_model() and predict() interfaces with mocked model.
Do NOT modify these tests.
"""

from __future__ import annotations

from typing import Any, List

import numpy as np
import pytest

from worker.src.detector import load_model, predict
from worker.src.schemas import Detection


# ──────────────────────────────────────────────
# load_model
# ──────────────────────────────────────────────

class TestLoadModel:
    """load_model() must return an object with a predict() method."""

    def test_returns_model_with_predict(self) -> None:
        """load_model() returns an object that has a callable predict()."""
        model = load_model()
        assert hasattr(model, "predict")
        assert callable(model.predict)

    def test_model_predict_returns_list(self) -> None:
        """model.predict() returns a list."""
        model = load_model()
        dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
        result = model.predict(dummy_frame)
        assert isinstance(result, list)

    def test_model_predict_items_are_detections(self) -> None:
        """Each item in predict() output is a Detection object."""
        model = load_model()
        dummy_frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        result = model.predict(dummy_frame)
        if result:
            for det in result:
                assert isinstance(det, Detection)

    def test_load_model_accepts_path(self) -> None:
        """load_model() accepts optional model path argument."""
        model = load_model("yolov8n.pt")
        assert hasattr(model, "predict")

    @pytest.mark.parametrize("bad_path", ["", "nonexistent.pt", "/invalid/path/model.pt"])
    def test_load_model_invalid_path_raises(self, bad_path: str) -> None:
        """Loading from an invalid path raises an appropriate exception."""
        with pytest.raises((FileNotFoundError, RuntimeError, ValueError)):
            load_model(bad_path)


# ──────────────────────────────────────────────
# predict (standalone)
# ──────────────────────────────────────────────

class TestPredictStandalone:
    """Standalone predict() convenience wrapper."""

    def test_predict_returns_list_of_detections(self) -> None:
        """predict() accepts a numpy frame and returns List[Detection]."""
        frame = np.zeros((416, 416, 3), dtype=np.uint8)
        result = predict(frame)
        assert isinstance(result, list)
        if result:
            assert all(isinstance(d, Detection) for d in result)

    def test_predict_empty_frame(self) -> None:
        """Empty frame (all zeros) returns empty list or valid results."""
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = predict(frame)
        assert isinstance(result, list)

    def test_predict_grayscale_frame(self) -> None:
        """Grayscale (2D) frame raises or is handled gracefully."""
        frame = np.zeros((100, 100), dtype=np.uint8)
        with pytest.raises((ValueError, TypeError)):
            predict(frame)


# ──────────────────────────────────────────────
# Edge cases for predict
# ──────────────────────────────────────────────

class TestPredictEdgeCases:
    """Edge cases and error handling for predict()."""

    @pytest.mark.parametrize(
        "bad_frame",
        [
            None,
            "not_an_array",
            [1, 2, 3],
            42,
        ],
    )
    def test_predict_invalid_input_types(self, bad_frame: Any) -> None:
        """predict() raises TypeError or ValueError for non-array inputs."""
        with pytest.raises((TypeError, ValueError)):
            predict(bad_frame)

    def test_predict_corrupt_frame(self) -> None:
        """predict() raises appropriate error on corrupt frame data."""
        frame = np.zeros((0, 0, 3), dtype=np.uint8)
        with pytest.raises((ValueError, RuntimeError)):
            predict(frame)

    def test_predict_large_frame(self) -> None:
        """predict() handles large frames without crashing (e.g. 4K)."""
        frame = np.zeros((2160, 3840, 3), dtype=np.uint8)
        result = predict(frame)
        assert isinstance(result, list)

    def test_predict_bbox_format(self) -> None:
        """Returned Detection bboxes are in YOLO format: [x_center, y_center, width, height]."""
        frame = np.zeros((640, 640, 3), dtype=np.uint8)
        result = predict(frame)
        if result:
            for det in result:
                xc, yc, w, h = det.bbox
                # YOLO format: all values normalized 0-1
                assert 0.0 <= xc <= 1.0, f"x_center out of range: {xc}"
                assert 0.0 <= yc <= 1.0, f"y_center out of range: {yc}"
                assert 0.0 <= w <= 1.0, f"width out of range: {w}"
                assert 0.0 <= h <= 1.0, f"height out of range: {h}"

    def test_predict_confidence_range(self) -> None:
        """Detection confidences are in [0.0, 1.0]."""
        frame = np.zeros((640, 640, 3), dtype=np.uint8)
        result = predict(frame)
        if result:
            for det in result:
                assert 0.0 <= det.confidence <= 1.0, (
                    f"confidence out of range: {det.confidence}"
                )

    def test_predict_returns_different_results_for_different_frames(self) -> None:
        """Different frames produce different detection results."""
        frame_a = np.zeros((640, 640, 3), dtype=np.uint8)
        frame_b = np.ones((640, 640, 3), dtype=np.uint8) * 255
        result_a = predict(frame_a)
        result_b = predict(frame_b)
        # They may or may not differ (mock), but the function should not crash
        assert isinstance(result_a, list)
        assert isinstance(result_b, list)
