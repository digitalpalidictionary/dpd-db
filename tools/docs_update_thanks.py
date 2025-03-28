"""Update mkdocs thanks."""

from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict
from tools.printer import printer as pr


def update_mkdocs_thanks():
    pth = ProjectPaths()
    thanks_data = ["# Thanks\n"]

    thanks = read_tsv_dot_dict(pth.thanks_tsv_path)

    for i in thanks:
        line = []
        if i.category:
            line += f"## {i.category}\n"
            line += f"{i.what}\n"
        if i.who:
            line += f"- **{i.who}**"
        if i.where:
            line += f" {i.where}"
        if i.what and not i.category:
            line += f" {i.what}"
        line += "\n"
        line_md = "".join(line)
        thanks_data.append(line_md)

    thanks_md = "".join(thanks_data)

    # save markdown for website
    pr.green("saving thanks to mkdocs")
    if pth.docs_thanks_md_path.exists():
        pth.docs_thanks_md_path.write_text(thanks_md)
        pr.yes("ok")
    else:
        pr.no("failed")
        pr.red(f"error saving {pth.docs_thanks_md_path}")


def main():
    pr.tic()
    pr.title("updating mkdocs thanks")
    update_mkdocs_thanks()
    pr.toc()


if __name__ == "__main__":
    main()
