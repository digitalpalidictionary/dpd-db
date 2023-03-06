import csv
import subprocess

from functions.get_paths import get_paths
pth = get_paths()


def add_sandhi_correction(window, values: dict) -> None:
    sandhi_to_correct = values["sandhi_to_correct"]
    sandhi_correction = values["sandhi_correction"]

    if sandhi_to_correct == "" or sandhi_correction == "":
        window["messages"].update(
            "you're shooting blanks!", text_color="red")

    elif " + " not in sandhi_correction:
        window["messages"].update(
            "no plus sign in sandhi correction!", text_color="red")

    else:

        with open(
                pth.sandhi_corrections_path, mode="a", newline="") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow([sandhi_to_correct, sandhi_correction])
            window["messages"].update(
                f"{sandhi_to_correct} > {sandhi_correction} added to corrections", text_color="white")
            window["sandhi_to_correct"].update("")
            window["chB"].update("")
            window["sandhi_correction"].update("")


def open_sandhi_corrections():
    subprocess.Popen(
        ["code", pth.sandhi_corrections_path])
