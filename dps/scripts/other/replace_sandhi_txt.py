# replace sandhi in txt and save it back

import json

from db.db_helpers import get_db_session
from tools.sandhi_contraction import make_sandhi_contraction_dict

from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from tools.sandhi_replacement import replace_sandhi

from rich.console import Console
from tools.printer import printer as pr

console = Console()


def main():
    pr.tic()

    pth: ProjectPaths = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)

    imput_txt_file = dpspth.text_to_add_path
    console.print(f"[bold yellow]replacing sandhi in the {imput_txt_file}")

    sandhi_dict = make_sandhi_contraction_dict(db_session)

    with open(pth.hyphenations_dict_path) as f:
        hyphenations_dict = json.load(f)

    if imput_txt_file:
        try:
            with open(imput_txt_file, "r") as f:
                text = f.read()
                text = text.strip()
                text = text.lower()
                text = text.replace("‘", "")
                text = text.replace(" – ", ", ")
                text = text.replace("’", "")
                text = text.replace("…pe॰…", " … ")
                text = text.replace("…pe…", " … ")
                text = text.replace("...", "…")
                text = text.replace(";", ",")
                text = text.replace("  ", " ")
                text = text.replace("..", ".")
                text = text.replace(" ,", ",")

        except FileNotFoundError:
            print(f"[red]file {imput_txt_file} does not exist")
            return set()

    replaced_text = replace_sandhi(text, sandhi_dict, hyphenations_dict)

    output_txt_file = imput_txt_file
    with open(output_txt_file, "w") as f:
        f.write(replaced_text)

    console.print(f"[bold green]replaced_text saved to {output_txt_file}")
    pr.toc()


if __name__ == "__main__":
    main()
