"""Update the mkdocs bibliography."""

from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_dot_dict


def _clean(value: str | None) -> str:
    """Collapse stray whitespace in a TSV cell.

    A newline inside a cell used to split the markdown mid-entry, stranding the
    closing italic marker on its own line and breaking the published page.
    """
    return " ".join(value.split()) if value else ""


def make_bibliography_md(pth: ProjectPaths) -> str:
    bibliography_data = ["# (An Incomplete) Bibliography\n"]
    bibliography_dict = read_tsv_dot_dict(pth.bibliography_tsv_path)

    for i in bibliography_dict:
        category = _clean(i.category)
        surname = _clean(i.surname)
        firstname = _clean(i.firstname)
        year = _clean(i.year)
        title = _clean(i.title)
        city = _clean(i.city)
        publisher = _clean(i.publisher)
        site = _clean(i.site)

        line = ""

        if category:
            line += f"## {category}\n\n"
        if surname:
            line += f"- **{surname}**"
        if firstname:
            line += f", {firstname}"
        if year:
            line += f", {year}"
        if title:
            line += f". *{title}*"
        if city and publisher:
            line += f", {city}: {publisher}"
        elif publisher:
            line += f", {publisher}"
        if site:
            line += f", accessed through [{site}]({site})"
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
