# PLAN — @ml/model-scientist

**Role**: YOLO integration, inference logic, `process_video()` implementation.

## Tasks

### 1.4 — Implement YOLO wrapper in `worker/src/detector.py`

- Load YOLOv8n (pretrained) via `ultralytics` library
- Interface: `load_model() -> Model`, `predict(frame: np.ndarray) -> List[Detection]`
- Wrap raw ultralytics output into typed `Detection` objects (class_id, class_name, confidence, bbox)
- Handle edge cases: empty frame, corrupt image, model load failure
- Must pass tests from task 1.3 (already written by @app/tester)

### 1.8 — Implement `process_video()` in `worker/src/processor.py`

- Signature: `process_video(job: JobInput) -> JobResult`
- Orchestration:
  1. Read video from S3 (via storage adapter)
  2. Iterate frames (extract every Nth frame? or all frames? configurable)
  3. Run detection per frame
  4. Aggregate results into JobResult
  5. Write JobResult JSON to S3 (via storage adapter)
  6. Return JobResult
- Must pass tests from task 1.7 (already written by @app/tester)

## Dependencies

- Task 1.4 depends on: 1.1 (schemas), 1.3 (tests exist)
- Task 1.8 depends on: 1.4 (detector), 1.6 (storage adapter), 1.7 (tests exist)

## Output Files

```
worker/src/
  detector.py     -- YOLO wrapper
  processor.py    -- process_video() orchestrator
```

## Verification

All tests in `tests/unit/test_detector.py` and `tests/unit/test_processor.py` must pass.
