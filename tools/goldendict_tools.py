import subprocess
import shutil
import sys
from pathlib import Path


def open_in_goldendict(word: str) -> None:
    exe = shutil.which("goldendict")

    if exe is None:
        if sys.platform == "win32":
            candidates: list[Path] = [
                Path("C:/Program Files/GoldenDict/GoldenDict.exe"),
                Path("C:/Program Files (x86)/GoldenDict/GoldenDict.exe"),
            ]
        elif sys.platform == "darwin":
            candidates = [
                Path("/Applications/GoldenDict.app/Contents/MacOS/GoldenDict"),
            ]
        else:
            candidates = []

        for candidate in candidates:
            if candidate.exists():
                exe = str(candidate)
                break

    if exe is None:
        return

    kwargs: dict = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if sys.platform == "win32":
        kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        kwargs["start_new_session"] = True

    subprocess.Popen([exe, word], **kwargs)
