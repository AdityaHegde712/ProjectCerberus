# PLAN — Phase 1 Video Decoding Fix

**Date**: 2026-07-10  
**Debugger**: Debugger Agent  
**Bug**: Phase 1 test failures — `error_message='Failed to decode video'`  
**Assigned To**: @ml/model-scientist (primary), @app/tester (verification)

---

## Overview

Fix the video decoding logic in `worker/src/processor.py` to properly handle in-memory video bytes by writing to a temporary file before passing to OpenCV.

---

## Implementation Tasks

### Task 1: Fix Video Decoding in processor.py

**Agent**: @ml/model-scientist  
**File**: `worker/src/processor.py`  
**Lines**: 39-48  
**Priority**: High

**Current Code (Lines 39-48)**:
```python
# Decode video using OpenCV
video_array = np.frombuffer(video_bytes, dtype=np.uint8)
cap = cv2.VideoCapture()

# Try to decode as MP4 first
if not cap.open(video_array.tobytes(), cv2.CAP_FFMPEG):
    # Try raw frame sequence
    video_array = np.frombuffer(video_bytes, dtype=np.uint8)
    cap = cv2.VideoCapture()
    if not cap.open(video_array.tobytes()):
        raise RuntimeError("Failed to decode video")
```

**Required Change**:
1. Add `import tempfile` and `import os` at the top of the file
2. Replace lines 39-48 with temporary file approach:
   - Write `video_bytes` to a temporary `.mp4` file
   - Open `cv2.VideoCapture()` with the file path
   - Wrap in `try/finally` to ensure cleanup
   - Remove the temporary file after processing

**New Code Structure**:
```python
import tempfile
import os
import cv2

# ... (inside process_video function)

# Decode video using OpenCV via temporary file
# OpenCV on Windows requires file path, not raw bytes
tmp_path = None
try:
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name
    
    cap = cv2.VideoCapture(tmp_path)
    if not cap.isOpened():
        raise RuntimeError("Failed to decode video")
    
    # ... (rest of processing remains unchanged)
    
finally:
    cap.release()
    if tmp_path and os.path.exists(tmp_path):
        os.unlink(tmp_path)
```

**Key Changes**:
- Remove the double-attempt logic (MP4 first, then raw)
- Use single `cv2.VideoCapture(path)` call
- Add `try/finally` for guaranteed cleanup
- Use `cap.isOpened()` instead of checking return value of `cap.open()`

---

### Task 2: Verify All Tests Pass

**Agent**: @app/tester  
**File**: `tests/unit/test_processor.py` (READ ONLY — do not modify)  
**Priority**: High

**Verification Steps**:
1. Run full test suite: `python -m pytest tests/unit/test_processor.py -v`
2. Confirm 20/20 tests pass
3. Verify no regressions in other test files
4. Run: `python -m pytest tests/ -v` to ensure no cross-module issues

**Expected Outcome**:
- All 9 previously failing tests now pass
- All 11 previously passing tests remain passing
- No new failures introduced

---

### Task 3: Code Review

**Agent**: @util/clean-coder  
**File**: `worker/src/processor.py`  
**Priority**: Medium

**Review Checklist**:
- [ ] Temp file cleanup is guaranteed (even on exceptions)
- [ ] No resource leaks (cap.release() in finally)
- [ ] Error messages are clear and actionable
- [ ] Code follows project style conventions
- [ ] No unnecessary imports added

---

## Execution Order

```
Task 1 (@ml/model-scientist)  →  Task 2 (@app/tester)  →  Task 3 (@util/clean-coder)
       [Fix implementation]           [Verify all pass]        [Code review]
```

**Critical**: Task 2 must confirm all tests pass before Task 3 proceeds.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Temp file cleanup failure | Low | Medium | `try/finally` guarantees cleanup |
| Temp file permission issues | Low | High | Use `tempfile` module (OS-managed) |
| Cross-platform compatibility | Low | Medium | `tempfile` works on all platforms |
| Performance impact (temp file I/O) | Low | Low | Negligible for video processing workload |

---

## Success Criteria

- [ ] All 20 tests in `test_processor.py` pass
- [ ] No regressions in other test files
- [ ] Code follows clean code principles
- [ ] Temp files are properly cleaned up
- [ ] No resource leaks

---

## Fallback Plan

If the temporary file approach fails (unlikely):
1. Investigate OpenCV build configuration for byte buffer support
2. Consider alternative video decoding libraries (e.g., imageio-ffmpeg)
3. Escalate to Owner for architectural decision

---

## Plan Version

- **Version**: 1.0
- **Status**: Ready for execution
- **Date**: 2026-07-10
