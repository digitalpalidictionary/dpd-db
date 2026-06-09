"""Update mkdocs thanks."""

from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_dot_dict


def make_thanks_md(pth: ProjectPaths) -> str:
    thanks_data = ["# Thanks\n"]
    thanks = read_tsv_dot_dict(pth.thanks_tsv_path)

    for i in thanks:
        line = ""
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
        thanks_data.append(line)

    return "".join(thanks_data)


def save_to_web(pth: ProjectPaths, thanks_md: str) -> None:
    pr.green_tmr("saving thanks to mkdocs")
    if pth.docs_thanks_md_path.exists():
        pth.docs_thanks_md_path.write_text(thanks_md, encoding="utf-8")
        pr.yes("ok")
    else:
        pr.no("failed")
        pr.red(f"error saving {pth.docs_thanks_md_path}")


def main() -> None:
    pr.tic()
    pr.yellow_title("updating mkdocs thanks")
    pth = ProjectPaths()
    thanks_md = make_thanks_md(pth)
    save_to_web(pth, thanks_md)
    pr.toc()


if __name__ == "__main__":
    main()
