import subprocess
from functions.get_paths import get_paths

pth = get_paths()


def open_internal_tests():
    subprocess.Popen(
        ["libreoffice", pth.internal_tests_path])
