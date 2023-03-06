import subprocess


def open_in_goldendict(word: str) -> None:
    cmd = ['goldendict', word]
    subprocess.Popen(cmd)
