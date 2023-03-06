import csv
from functions.get_paths import get_paths


def sandhi_ok(window, word,):
    pth = get_paths()
    with open(pth.sandhi_ok_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([word])
    window["messages"].update(f"{word} added", text_color="white")
