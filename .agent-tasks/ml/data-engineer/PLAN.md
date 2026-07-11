# PLAN — @ml/data-engineer

**Role**: Data schema definitions, storage adapter, data I/O abstractions.

## Tasks

### 1.2 — Implement data schema models in `worker/src/schemas.py`

Define Pydantic models:

```python
class Detection(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: tuple[float, float, float, float]  # YOLO format: [x_center, y_center, width, height] (normalized 0-1)

class JobInput(BaseModel):
    job_id: str
    video_s3_key: str
    input_bucket: str
    frame_step: int = 1  # process every Nth frame

class JobResult(BaseModel):
    job_id: str
    status: Literal["completed", "failed"]
    frames_processed: int
    detections: list[tuple[int, list[Detection]]]  # (frame_index, detections[])
    output_s3_key: str
    worker_type: str
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None
```

Must pass tests from task 1.1.

### 1.6 — Implement S3 storage adapter in `worker/src/storage.py`

- Interface: `read_video(key: str) -> bytes`, `write_json(key: str, data: dict) -> None`
- Local file fallback mode (no AWS credentials needed for test/dev)
- S3 mode using `boto3`
- Must pass tests from task 1.5.

## Output Files

```
worker/src/
  schemas.py   -- Pydantic models
  storage.py   -- S3/local storage adapter
```

## Verification

All tests in `tests/unit/test_schemas.py` and `tests/unit/test_storage.py` must pass.
