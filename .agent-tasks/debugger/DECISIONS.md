# DECISIONS — Phase 1 Test Failures

**Date**: 2026-07-10  
**Debugger**: Debugger Agent  
**Bug Severity**: High (blocks Phase 1 completion)

---

## Bug Summary

**Symptom**: 9 out of 20 unit tests in `test_processor.py` fail with `error_message='Failed to decode video'`.

**Root Cause**: `processor.py` lines 39-48 attempts to decode video from raw bytes using `cv2.VideoCapture().open(bytes_buffer)`. OpenCV's `VideoCapture.open()` on Windows does **not support raw byte buffers** — it requires a file path string or camera index. The call silently returns `False`, the fallback also fails, and it raises `RuntimeError("Failed to decode video")`.

**Affected Component**: `worker/src/processor.py` — video decoding section (lines 39-48)

**Environment**: Windows, Python 3.13.6, OpenCV (cv2)

**Reproduces**: Consistently (100% reproduction rate)

---

## Hypothesis (Confirmed)

> "The bug occurs because `cv2.VideoCapture.open()` on Windows requires a file path or camera index, not raw byte buffers. When passed `video_array.tobytes()`, the method returns `False`, triggering the fallback which also fails, ultimately raising `RuntimeError("Failed to decode video")`. I expect to confirm this by the 9 failing tests that all provide valid .mp4 bytes via `_make_test_video_bytes()`."

**Verification**: Test output confirms all 9 failures have identical error message. The 11 passing tests are those that don't require successful video decoding (e.g., empty video, storage read failure, detector crashes).

---

## Fix Decision

**Chosen Approach**: Write bytes to temporary file, pass path to OpenCV, clean up after processing.

**Rationale**:
1. This is the **standard pattern** for in-memory video processing with OpenCV on Windows
2. It's a **minimal diff** — only the video decoding section changes
3. It's **cross-platform compatible** — works on Windows, Linux, and macOS
4. It **preserves intent** — the code does what it was designed to do, just with proper file I/O
5. It's **defensive** — includes proper cleanup in `finally` block

**Alternative Considered**: Memory-mapped file or other buffer approach. Rejected because it adds complexity without clear benefit for this use case.

---

## Approval Status

- [x] Root cause confirmed
- [x] Fix approach approved by Owner (via bug report)
- [ ] Implementation pending
- [ ] Verification pending

---

## Related Files

- `worker/src/processor.py` — Implementation to fix
- `tests/unit/test_processor.py` — LOCKED tests (do NOT modify)
- `.agent-tasks/debugger/PLAN.md` — Implementation plan
