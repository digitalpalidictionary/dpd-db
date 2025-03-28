"""Update the mkdocs bibliography."""

from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict
from tools.printer import printer as pr


def update_mkdocs_bibliography():
    pth = ProjectPaths()
    bibliography_data = ["# (An Incomplete) Bibliography\n"]

    file_path = pth.bibliography_tsv_path
    bibliography_dict = read_tsv_dot_dict(file_path)

    for i in bibliography_dict:
        line = []

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
        if not i.city and i.publisher:
            line += f", {i.publisher}"
        if i.site:
            line += f", accessed through [{i.site}]({i.site})"
        line += "\n"
        line_md = "".join(line)
        bibliography_data.append(line_md)

    bibliography_md = "".join(bibliography_data)

    # save markdown for mkdocs website
    pr.green("saving bibliography to mkdocs")
    if pth.docs_bibliography_md_path.exists():
        pth.docs_bibliography_md_path.write_text(bibliography_md)
        pr.yes("ok")
    else:
        pr.no("failed")
        pr.red(f"bibliography path {pth.docs_thanks_md_path} doesn't exist ")


def main():
    pr.tic()
    pr.title("updating mkdocs bibliography")
    update_mkdocs_bibliography()
    pr.toc()


if __name__ == "__main__":
    main()
