from mako.template import Template
from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from db.models import DerivedData

from tools.meaning_construction import make_meaning_html
from tools.meaning_construction import summarize_constr
from tools.meaning_construction import degree_of_completion

from tools.pali_alphabet import pali_alphabet
from tools.first_letter import find_first_letter
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths as PTH
from tools.timeis import tic, toc


ebook_entry_templ = Template(
    filename=str(PTH.ebook_entry_templ_path))
ebook_letter_tmpl = Template(
    filename=str(PTH.ebook_letter_templ_path))
ebook_header_tmpl = Template(
    filename=str(PTH.ebook_header_templ_path))


def main():
    tic()
    print("[bright_yellow]rendering dpd for ebook")

    db_sesssion = get_db_session("dpd.db")
    dpd_db = db_sesssion.query(PaliWord).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.pali_1))

    dd_db = db_sesssion.query(DerivedData).all()
    dd_dict = {}
    for i in dd_db:
        dd_dict[i.id] = i.inflections_list

    # a dicitonary for entries of each letter of the alphabet
    letter_dict: dict = {}
    for letter in pali_alphabet:
        letter_dict[letter] = []

    print("[green]creating entries")
    for counter, i in enumerate(dpd_db):
        first_letter = find_first_letter(i)
        # entry = render_ebook_entry(counter, i, i.dd.inflections_list)
        entry = render_ebook_entry(counter, i, dd_dict[i.id])
        letter_dict[first_letter] += [entry]

        if counter % 5000 == 0:
            print(f"{counter:>10,} / {len(dpd_db):<10,} {i.pali_1}")

    print("[green]saving entries")
    total = 0
    for counter, (letter, entries) in enumerate(letter_dict.items()):
        length = len(entries)
        total += length
        entries = "".join(entries)
        xhtml = render_ebook_letter_tmpl(letter, entries)

        output_path = PTH.ebook_output_text_dir.joinpath(
            f"{counter}. {letter}.xhtml")

        with open(output_path, "w") as f:
            f.write(xhtml)

        print(f"{length:>10,} : {letter:<5}")
    print(f"{total:>10,} : {'total':<5}")
    toc()


def render_ebook_entry(counter: int, i: PaliWord, inflections: list) -> str:
    """Render single word entry."""

    summary = f"{i.pos}. "
    if i.plus_case:
        summary += f"({i.plus_case}) "
    summary += make_meaning_html(i)

    construction = summarize_constr(i)
    if construction:
        summary += f" [{construction}]"

    summary += f" {degree_of_completion(i)}"

    if "&" in summary:
        summary = summary.replace("&", "and")

    return str(ebook_entry_templ.render(
            counter=counter,
            pali_1=i.pali_1,
            pali_clean=i.pali_clean,
            inflections=inflections,
            summary=summary))


def render_ebook_letter_tmpl(letter: str, entries: str) -> str:
    """Render entries for a single letter."""
    return str(
        ebook_letter_tmpl.render(
            letter=letter,
            entries=entries))


def render_ebook_header_tmpl(css: str, entries: str) -> str:
    """Render the entire ebook."""
    return str(
        ebook_header_tmpl.render(
            css=css,
            entries=entries))


if __name__ == "__main__":
    main()
