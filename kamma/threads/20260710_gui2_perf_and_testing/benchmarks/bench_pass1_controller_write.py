"""8.3: before/after for the Phase 8.1 fix in Pass1AutoController.add_word()/
remove_word() — dropped a redundant Pass1FileManager.read() call that
followed every Pass1FileManager.update() call (update() already returns the
updated dict; the extra read just re-read the same file from disk).

"before" replays the old code path directly (update() then a separate
read()); "after" calls the now-fixed add_word(). Same sandboxed copy of the
real per-book file, same single-edit shape as bench_json_write.py's 3.7
measurement.
"""

import shutil
import time
from pathlib import Path

from bench_common import RESULTS_DIR, write_result

REAL_PASS1_DHPA = Path(
    "/home/bodhirasa/MyFiles/3_Active/dpd-db/gui2/data/pass1_auto_dhpa.json"
)
SANDBOX = RESULTS_DIR.parent / "pass1_controller_write_sandbox"


def setup_sandbox() -> Path:
    if SANDBOX.exists():
        shutil.rmtree(SANDBOX)
    data_dir = SANDBOX / "gui2" / "data"
    data_dir.mkdir(parents=True)
    shutil.copy(REAL_PASS1_DHPA, data_dir / "pass1_auto_dhpa.json")
    return SANDBOX


def main() -> None:
    from gui2.paths import Gui2Paths
    from gui2.pass1_file_manager import Pass1FileManager
    from gui2.pass1_auto_controller import Pass1AutoController

    sandbox = setup_sandbox()
    paths = Gui2Paths(base_dir=sandbox)
    size_mb = (paths.gui2_data_path / "pass1_auto_dhpa.json").stat().st_size / (
        1024 * 1024
    )

    def noop_update(data: dict) -> None:
        data["_bench_marker"] = True

    # --- before: old code path (update() then a separate, redundant read()) ---
    fm_before = Pass1FileManager(paths)
    start = time.perf_counter()
    fm_before.update("dhpa", noop_update)
    fm_before.read("dhpa")
    before_ms = (time.perf_counter() - start) * 1000

    # --- after: Pass1AutoController.add_word(), using update()'s return value ---
    controller = object.__new__(Pass1AutoController)
    controller.file_manager = Pass1FileManager(paths)
    controller.book = "dhpa"
    start = time.perf_counter()
    controller.add_word("dhpa", "_bench_word", {"lemma_1": "x"})
    after_ms = (time.perf_counter() - start) * 1000

    result = {
        "pass1_auto_dhpa_size_mb": round(size_mb, 2),
        "before_update_plus_extra_read_ms": round(before_ms, 2),
        "after_add_word_ms": round(after_ms, 2),
    }

    print(
        f"Pass1AutoController per-word file write on {size_mb:.2f} MB file: "
        f"before (update()+redundant read()) {before_ms:.2f} ms, "
        f"after (add_word(), no redundant read) {after_ms:.2f} ms"
    )

    write_result("8.3_pass1_controller_write", result)
    shutil.rmtree(sandbox)


if __name__ == "__main__":
    main()
