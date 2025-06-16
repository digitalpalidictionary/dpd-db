# -*- coding: utf-8 -*-
"""
Find specific deconstructions in the 1GB matches.tsv file,
and save to a temp file.
"""

from tools.paths import ProjectPaths
from tools.printer import printer as pr
from rich import print

find_me = "kaṭṭhattharaṇapaṇṇattharaṇaāsanādīni"


def write_temp_file(found: list[str]):
    print("written to ", end="")
    temp_file = "temp/deconstruction_finder.csv"
    with open(temp_file, "w") as f:
        f.write("".join(found))
    print(f"[blue]{temp_file}")


def find_deconstructions(find_me: str):
    pr.title("finding deconstructions")

    p = ProjectPaths()
    file_path = p.go_deconstructor_output_dir.joinpath("matches.tsv")

    found: list[str] = []

    pr.green_title("parsing matches.tsv")
    with open(file_path, "r") as f:
        for line_number, line in enumerate(f):
            if line_number == 0:
                found.append(line)

            sections: list[str] = line.split("\t")
            # if find_me in line:
            # if line.startswith(find_me):
            if find_me in sections[0]:
                # if sections[0] == find_me:
                found.append(line)

    write_temp_file(found)


if __name__ == "__main__":
    find_deconstructions(find_me)
