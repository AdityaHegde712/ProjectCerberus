import os
import tempfile
from datetime import datetime, timezone
from typing import List, Tuple

import cv2
import numpy as np

from worker.src import storage
from worker.src import detector
from worker.src.schemas import Detection, JobInput, JobResult


def _build_result_data(
    job: JobInput,
    frames_processed: int,
    detections_result: List[Tuple[int, List[Detection]]],
    output_key: str,
    started_at: datetime,
) -> dict:
    """Build a serializable result data dict for storage output.

    Uses JobResult.model_dump() to get consistent field names and
    ISO-formatted timestamps, then overrides the detections field with
    the processed format (frame_index + detections list).
    """
    result = JobResult(
        job_id=job.job_id,
        status="completed",
        frames_processed=frames_processed,
        detections=detections_result,
        output_s3_key=output_key,
        worker_type="yolo-detector",
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
    )
    result_data = result.model_dump(mode="json")
    # Override detections with processed format (frame_index + detections list)
    result_data["detections"] = [
        {
            "frame_index": frame_idx,
            "detections": [
                {
                    "class_id": det.class_id,
                    "class_name": det.class_name,
                    "confidence": det.confidence,
                    "bbox": det.bbox,
                }
                for det in detections
            ],
        }
        for frame_idx, detections in detections_result
    ]
    return result_data


def process_video(job: JobInput) -> JobResult:
    """
    Process a video file by running YOLO detection on selected frames.
    
    Args:
        job: JobInput containing video path, frame_step, and other metadata.
        
    Returns:
        JobResult with processing status, detections, and metadata.
    """
    started_at = datetime.now(timezone.utc)
    
    try:
        # Read video bytes from storage
        video_bytes = storage.read_video(job.video_s3_key)
        
        if not video_bytes:
            return JobResult(
                job_id=job.job_id,
                status="failed",
                frames_processed=0,
                detections=[],
                output_s3_key="",
                worker_type="yolo-detector",
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                error_message="Video file is empty"
            )
        
        # Decode video using OpenCV via temporary file
        # OpenCV on Windows requires file path, not raw bytes
        tmp_path = None
        cap = cv2.VideoCapture()
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp_path = tmp.name
                tmp.write(video_bytes)
            
            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                raise RuntimeError(f"Failed to decode video at temporary file: {tmp_path}")
            
            # Get video properties
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Process frames according to frame_step
            detections_result: List[Tuple[int, List[Detection]]] = []
            frames_processed = 0
            
            for frame_idx in range(0, frame_count, job.frame_step):
                # Seek to frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                
                # Read frame
                ret, frame = cap.read()
                if not ret:
                    continue
                    
                # Convert BGR to RGB (OpenCV uses BGR)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Run detection
                frame_detections = detector.predict(frame_rgb)
                
                detections_result.append((frame_idx, frame_detections))
                frames_processed += 1
        finally:
            if cap is not None:
                cap.release()
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        # Generate output key
        output_key = f"results/{job.job_id}_detections.json"
        
        # Prepare result data for storage
        result_data = _build_result_data(
            job, frames_processed, detections_result, output_key, started_at
        )
        
        # Write results to storage
        storage.write_json(output_key, result_data)
        
        return JobResult(
            job_id=job.job_id,
            status="completed",
            frames_processed=frames_processed,
            detections=detections_result,
            output_s3_key=output_key,
            worker_type="yolo-detector",
            started_at=started_at,
            completed_at=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        # Handle any errors during processing
        error_msg = str(e)
        
        # Try to write error result to storage if possible
        try:
            error_key = f"results/{job.job_id}_error.json"
            error_data = {
                "job_id": job.job_id,
                "status": "failed",
                "frames_processed": 0,
                "detections": [],
                "output_s3_key": error_key,
                "worker_type": "yolo-detector",
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "error_message": error_msg
            }
            storage.write_json(error_key, error_data)
        except Exception:
            pass  # Ignore write errors from storage
        
        return JobResult(
            job_id=job.job_id,
            status="failed",
            frames_processed=0,
            detections=[],
            output_s3_key="",
            worker_type="yolo-detector",
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            error_message=error_msg
        )