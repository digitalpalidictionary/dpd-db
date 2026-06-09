"""Update the mkdocs bibliography."""

from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_dot_dict


def make_bibliography_md(pth: ProjectPaths) -> str:
    bibliography_data = ["# (An Incomplete) Bibliography\n"]
    bibliography_dict = read_tsv_dot_dict(pth.bibliography_tsv_path)

    for i in bibliography_dict:
        line = ""

        if i.category:
            line += f"## {i.category}\n\n"
        if i.surname:
            line += f"- **{i.surname}**"
        if i.firstname:
            line += f", {i.firstname}"
        if i.year:
            line += f", {i.year}"
        if i.title:
            line += f". *{i.title}*"
        if i.city and i.publisher:
            line += f", {i.city}: {i.publisher}"
        elif i.publisher:
            line += f", {i.publisher}"
        if i.site:
            line += f", accessed through [{i.site}]({i.site})"
        line += "\n"
        bibliography_data.append(line)

    return "".join(bibliography_data)


def save_to_web(pth: ProjectPaths, bibliography_md: str) -> None:
    pr.green_tmr("saving bibliography to mkdocs")
    if pth.docs_bibliography_md_path.exists():
        pth.docs_bibliography_md_path.write_text(bibliography_md, encoding="utf-8")
        pr.yes("ok")
    else:
        pr.no("failed")
        pr.red(f"bibliography path {pth.docs_bibliography_md_path} doesn't exist")


def main() -> None:
    pr.tic()
    pr.yellow_title("updating mkdocs bibliography")
    pth = ProjectPaths()
    bibliography_md = make_bibliography_md(pth)
    save_to_web(pth, bibliography_md)
    pr.toc()


if __name__ == "__main__":
    main()
