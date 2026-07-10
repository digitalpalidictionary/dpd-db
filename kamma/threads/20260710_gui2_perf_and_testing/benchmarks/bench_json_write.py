"""3.7: JSON write amplification — time a single Pass1FileManager.update()
call (full read+write of the whole per-book file) and a single
Pass2AutoFileManager.update_pass2_auto_data() call (full read+write),
against throwaway copies of the real data files.

Note: the real gui2/data/pass2_auto.json is currently near-empty (2 bytes,
already drained by contributors), so it isn't representative of the
"queue full of pending items" state this manager normally handles. This
script synthesizes a 5000-entry pass2_auto.json (a plausible mid-size
queue) into the throwaway copy so the write-amplification cost is
measurable; the real file is never touched.
"""

import json
import shutil
import time
from pathlib import Path

from bench_common import RESULTS_DIR, write_result

REAL_PASS1_DHPA = Path(
    "/home/bodhirasa/MyFiles/3_Active/dpd-db/gui2/data/pass1_auto_dhpa.json"
)
SANDBOX = RESULTS_DIR.parent / "json_write_sandbox"


def setup_sandbox() -> Path:
    if SANDBOX.exists():
        shutil.rmtree(SANDBOX)
    data_dir = SANDBOX / "gui2" / "data"
    data_dir.mkdir(parents=True)

    shutil.copy(REAL_PASS1_DHPA, data_dir / "pass1_auto_dhpa.json")

    # Synthesize a representative mid-size pass2_auto queue (real file is
    # currently near-empty, see module docstring).
    synthetic_pass2_auto = {
        str(i): {
            "lemma_1": f"word{i}",
            "meaning_1": f"meaning of word {i}, a placeholder gloss",
            "grammar": "pr. 3sg.",
        }
        for i in range(5000)
    }
    (data_dir / "pass2_auto.json").write_text(
        json.dumps(synthetic_pass2_auto, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )

    return SANDBOX


def main() -> None:
    sandbox = setup_sandbox()

    from gui2.paths import Gui2Paths

    paths = Gui2Paths(base_dir=sandbox)

    # --- Pass1FileManager.update() : full read+write of the per-book file ---
    from gui2.pass1_file_manager import Pass1FileManager

    pass1_size_mb = (paths.gui2_data_path / "pass1_auto_dhpa.json").stat().st_size / (
        1024 * 1024
    )
    fm1 = Pass1FileManager(paths)

    def noop_update(data: dict) -> None:
        data["_bench_marker"] = True

    start = time.perf_counter()
    fm1.update("dhpa", noop_update)
    pass1_update_ms = (time.perf_counter() - start) * 1000

    # --- Pass2AutoFileManager.update_pass2_auto_data() : full read+write ---
    from gui2.toolkit import ToolKit
    from gui2.pass2_auto_file_manager import Pass2AutoFileManager

    toolkit = object.__new__(ToolKit)
    toolkit.paths = paths
    pass2_size_mb = (paths.gui2_data_path / "pass2_auto.json").stat().st_size / (
        1024 * 1024
    )
    fm2 = Pass2AutoFileManager(toolkit)

    start = time.perf_counter()
    fm2.update_pass2_auto_data("9999", {"lemma_1": "new_word", "meaning_1": "x"})
    pass2_update_ms = (time.perf_counter() - start) * 1000

    result = {
        "pass1_auto_dhpa_size_mb": round(pass1_size_mb, 2),
        "pass1_file_manager_update_ms": round(pass1_update_ms, 2),
        "pass2_auto_synthetic_entries": 5000,
        "pass2_auto_size_mb": round(pass2_size_mb, 2),
        "pass2_auto_file_manager_update_ms": round(pass2_update_ms, 2),
    }

    print(
        f"Pass1FileManager.update() on {pass1_size_mb:.2f} MB file: "
        f"{pass1_update_ms:.2f} ms (full read+write per single edit)"
    )
    print(
        f"Pass2AutoFileManager.update_pass2_auto_data() on {pass2_size_mb:.2f} MB "
        f"file (5000 synthetic entries): {pass2_update_ms:.2f} ms "
        f"(full read+write per single edit)"
    )

    write_result("3.7_json_write", result)
    shutil.rmtree(sandbox)


if __name__ == "__main__":
    main()
