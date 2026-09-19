# Run timed_gui.py three times, killing each launch's whole process group
# the moment ALL TABS WARMED prints. Appends stamps to phase3_serial.log.

import os
import subprocess
import time
from pathlib import Path

HARNESS = Path(
    "kamma/threads/20260918_gui2_startup_latency/artifacts/timed_gui.py"
)
LOG = HARNESS.parent / "phase3_serial.log"

env = {**os.environ, "PYTHONPATH": "."}

with open(LOG, "w") as log:
    for run in range(1, 4):
        log.write(f"=== run {run} ===\n")
        log.flush()
        out_path = Path(f"/tmp/gui_run_{run}.log")
        with open(out_path, "wb") as out:
            proc = subprocess.Popen(
                [
                    "xvfb-run",
                    "-a",
                    "-s",
                    "-screen 0 1280x800x24",
                    "uv",
                    "run",
                    "python",
                    str(HARNESS),
                ],
                cwd=".",
                env=env,
                stdout=out,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        deadline = time.time() + 90
        warmed = False
        while time.time() < deadline:
            if "ALL TABS WARMED" in out_path.read_text(errors="replace"):
                warmed = True
                time.sleep(1)
                break
            if proc.poll() is not None:
                break
            time.sleep(1)
        os.killpg(proc.pid, 15)
        time.sleep(2)
        try:
            os.killpg(proc.pid, 9)
        except ProcessLookupError:
            pass
        proc.wait()
        stamps = [
            line
            for line in out_path.read_text(errors="replace").splitlines()
            if line.startswith("[startup]")
        ]
        log.write("\n".join(stamps) + ("\n" if stamps else ""))
        log.write(f"(warmed stamp seen: {warmed})\n")
        log.flush()
        time.sleep(1)
    # leftover check
    ps = subprocess.run(
        ["ps", "-eo", "cmd"], capture_output=True, text=True
    ).stdout
    leftovers = [
        line
        for line in ps.splitlines()
        if "timed_gui" in line or "flet/flet" in line
    ]
    log.write(f"leftovers: {leftovers or 'none'}\n")
print("done")
