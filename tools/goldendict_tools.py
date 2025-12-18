import subprocess
import os


def open_in_goldendict(word: str) -> None:
    cmd = ["goldendict", word]
    subprocess.Popen(cmd)


def open_in_goldendict_os(word: str) -> None:
    cmd = "nohup goldendict " + word + " > /dev/null 2>&1 &"
    os.system(cmd)
