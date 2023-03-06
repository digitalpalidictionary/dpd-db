import csv
import subprocess

from functions.get_paths import get_paths
pth = get_paths()


def add_spelling_mistake(window, values: dict) -> None:
    spelling_mistake = values["spelling_mistake"]
    spelling_correction = values["spelling_correction"]

    if spelling_mistake == "" or spelling_correction == "":
        window["messages"].update(
            "you're shooting blanks!", text_color="red")

    else:

        with open(
                pth.spelling_corrections_path, mode="a", newline="") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow([spelling_mistake, spelling_correction])
            window["messages"].update(
                f"{spelling_mistake} > {spelling_correction} added to spelling mistakes", text_color="white")
            window["spelling_mistake"].update("")
            window["spelling_correction"].update("")


def open_spelling_mistakes():
    subprocess.Popen(
        ["code", pth.spelling_corrections_path])
