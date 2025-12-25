# Plan: Audio Migration

## Phase 1: Migration & Ignoring
- [x] **Task 1.1:** Create root `audio/` directory structure. <!-- 3fdc3f5 -->
- [x] **Task 1.2:** Copy logic and scripts from `resources/dpd_audio/` to `audio/`. <!-- a36de68 -->
- [x] **Task 1.3:** Update root `.gitignore` to ignore `audio/mp3s/` and `audio/db/dpd_audio.db`. <!-- 2839fdd -->
- [x] **Task 1.4:** Verify `git status` reflects correct tracking (code in, data out). <!-- 87642a5 -->

## Phase 2: Path Updates
- [x] **Task 2.1:** Update `tools/paths.py` with new `audio/` root paths.
- [x] **Task 2.2:** Search for hardcoded `resources/dpd_audio` strings and update to `audio/`.

## Phase 3: Documentation & Verification
- [x] **Task 3.1:** Create/Update `resources/dpd_audio/README.md` with release instructions.
- [x] **Task 3.2:** Run a test script from the new `audio/` folder to verify paths (e.g., scan logic).

## Phase 4: Submodule History Cleanup (resources/dpd_audio/)
- [x] **Task 4.1:** Create orphan branch and reset submodule to single README commit.
- [x] **Task 4.2:** Verify tags still exist locally and point to historical states.
- [x] **Task 4.3:** (Manual Step) Force push cleaned main to submodule remote. <!-- manual completion confirmed -->

## Phase 5: Submodule Retention
- [x] **Task 5.1:** Decision made to retain the submodule as a staging area for releases. <!-- user decision -->