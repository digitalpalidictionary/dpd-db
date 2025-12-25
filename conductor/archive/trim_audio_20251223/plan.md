# Plan: Trim Audio

## Phase 1: Foundation
- [x] **Task 1.1:** Scaffold `trim_audio.py` with necessary imports and configuration (Path, subprocess, multiprocessing).
- [x] **Task 1.2:** Adapt `gather_mp3_files` from `silent_files.py` to target the correct directories.

## Phase 2: Core Logic
- [x] **Task 2.1:** Implement `get_silence_info(filepath)` using `ffmpeg -af silencedetect`.
- [x] **Task 2.2:** Implement `trim_file(filepath, start, end)` using `ffmpeg` to extract the desired segment with 100ms padding.
- [x] **Task 2.3:** Implement the main processing loop with `multiprocessing.Pool`.

## Phase 3: Verification
- [x] **Task 3.1:** Run the script on a subset of files and verify the `_trimmed.mp3` outputs manually.

## Phase 4: Refinement and Deployment
- [x] **Task 4.1:** Update `trim_file` to support overwriting (save to temp, then move).
- [x] **Task 4.2:** Implement `TRIM_THRESHOLD_MS` logic in `process_one_file` to skip files with negligible silence.
- [x] **Task 4.3:** Verify the logic on a small batch before full run.