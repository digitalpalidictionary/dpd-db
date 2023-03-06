import csv
import subprocess

from functions.get_paths import get_paths
pth = get_paths()


def add_variant_reading(window, values: dict) -> None:
    variant_reading = values["variant_reading"]
    main_reading = values["main_reading"]

    if variant_reading == "" or main_reading == "":
        window["messages"].update(
            "you're shooting blanks!", text_color="red")

    else:
        with open(
                pth.variant_readings_path, mode="a", newline="") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow([variant_reading, main_reading])
            window["messages"].update(
                f"{variant_reading} > {main_reading} added to variant readings", text_color="white")
            window["variant_reading"].update("")
            window["main_reading"].update("")


def open_variant_readings():
    subprocess.Popen(
        ["code", pth.variant_readings_path])
