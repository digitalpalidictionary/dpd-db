import subprocess
from functions.get_paths import get_paths

pth = get_paths()


def open_inflection_tables():
    subprocess.Popen(
        ["libreoffice", pth.inflection_templates_path])
