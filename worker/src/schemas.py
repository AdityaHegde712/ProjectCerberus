from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, field_validator


class Detection(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: tuple[float, float, float, float]  # YOLO format: [x_center, y_center, width, height] (normalized 0-1)
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('confidence must be between 0.0 and 1.0')
        return v
    
    @field_validator('bbox')
    @classmethod
    def validate_bbox(cls, v):
        x_center, y_center, width, height = v
        if not (0.0 <= x_center <= 1.0):
            raise ValueError('x_center must be between 0.0 and 1.0')
        if not (0.0 <= y_center <= 1.0):
            raise ValueError('y_center must be between 0.0 and 1.0')
        if not (0.0 < width <= 1.0):
            raise ValueError('width must be between 0.0 and 1.0 (exclusive of 0)')
        if not (0.0 < height <= 1.0):
            raise ValueError('height must be between 0.0 and 1.0 (exclusive of 0)')
        return v


class JobInput(BaseModel):
    job_id: str
    video_s3_key: str
    input_bucket: str
    frame_step: int = 1  # process every Nth frame
    
    @field_validator('frame_step')
    @classmethod
    def validate_frame_step(cls, v):
        if v <= 0:
            raise ValueError('frame_step must be positive')
        return v


class JobResult(BaseModel):
    job_id: str
    status: Literal["completed", "failed"]
    frames_processed: int
    detections: list[tuple[int, list[Detection]]]  # (frame_index, detections[])
    output_s3_key: str
    worker_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None