"""Debug tool: find a specific compound's deconstruction in the 1GB matches.tsv file.

Edit `find_me` below to the word you're debugging, then run. Matching lines
(plus the header) are saved to `temp/deconstruction_finder.csv`.
"""

from rich import print

from tools.paths import ProjectPaths
from tools.printer import printer as pr

find_me = "kaṭṭhattharaṇapaṇṇattharaṇaāsanādīni"


def write_temp_file(found: list[str]) -> None:
    """Write the matched lines to a temp CSV file."""
    print("written to ", end="")
    pth = ProjectPaths()
    temp_file = pth.temp_dir / "deconstruction_finder.csv"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write("".join(found))
    print(f"[blue]{temp_file}")


def find_deconstructions(find_me: str) -> None:
    """Find every line in matches.tsv whose first column contains find_me."""
    pr.yellow_title("finding deconstructions")

    p = ProjectPaths()
    file_path = p.go_deconstructor_output_dir.joinpath("matches.tsv")

    found: list[str] = []

    pr.green_title("parsing matches.tsv")
    with open(file_path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f):
            if line_number == 0:
                found.append(line)

            sections: list[str] = line.split("\t")
            if find_me in sections[0]:
                found.append(line)

    write_temp_file(found)


if __name__ == "__main__":
    find_deconstructions(find_me)
