# Specification: Trim Audio

## Overview
Update `resources/dpd_audio/error_check/trim_audio.py` to trim excess silence from the beginning and end of MP3 files using `ffmpeg`. The script will overwrite the original files if significant silence is detected.

## Functional Requirements
1.  **File Discovery:** Locate MP3 files in the audio directory.
2.  **Silence Detection:** Use `ffmpeg` with the `silencedetect` filter to find the start and end of actual audio.
3.  **Smart Trimming:**
    *   Preserve a **100ms** buffer at both ends.
    *   **Skip trimming** if the total reduction in duration is less than **50ms** (configurable threshold) to avoid unnecessary file churn.
4.  **Overwrite Mode:** Save the trimmed audio directly over the original file (no `_trimmed` suffix).
5.  **Parallel Execution:** Use `multiprocessing` to process multiple files simultaneously.

## Non-Functional Requirements
1.  **High Performance:** Leverage `ffmpeg`'s speed and Python's `multiprocessing`.
2.  **Safety:** Use atomic writes (write to temp, then rename) to prevent corruption.

## Acceptance Criteria
- [ ] Script overwrites original files only when necessary.
- [ ] Files with minimal silence (<50ms removable) are left untouched.
- [ ] Files with significant silence are trimmed to have exactly ~100ms padding.
- [ ] No automated tests are required; manual listening is the success criterion.

## Out of Scope
- Automated tests.