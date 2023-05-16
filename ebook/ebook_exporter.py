from mako.template import Template
from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord, Sandhi
from db.models import DerivedData

from tools.meaning_construction import make_meaning_html
from tools.meaning_construction import summarize_constr
from tools.meaning_construction import degree_of_completion

from tools.cst_sc_text_sets import make_cst_text_set
from tools.cst_sc_text_sets import make_sc_text_set
from tools.pali_alphabet import pali_alphabet
from tools.first_letter import find_first_letter
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths as PTH
from tools.sandhi_words import make_words_in_sandhi_set
from tools.timeis import tic, toc


ebook_entry_templ = Template(
    filename=str(PTH.ebook_entry_templ_path))
ebook_sandhi_templ = Template(
    filename=str(PTH.ebook_sandhi_templ_path))
ebook_letter_tmpl = Template(
    filename=str(PTH.ebook_letter_templ_path))


def main():
    tic()
    print("[bright_yellow]rendering dpd for ebook")

    print(f"[green]{'querying dpd db':<40}", end="")
    db_sesssion = get_db_session("dpd.db")
    dpd_db = db_sesssion.query(PaliWord).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.pali_1))
    print(f"{len(dpd_db):>10,}")

    # limit the extent of the dictionary to an ebt text set
    ebt_books = [
        "vin1", "vin2", "vin3", "vin4",
        "dn1", "dn2", "dn3",
        "mn1", "mn2", "mn3",
        "sn1", "sn2", "sn3", "sn4", "sn5",
        "an1", "an2", "an3", "an4", "an5",
        "an6", "an7", "an8", "an9", "an10", "an11",
        "kn1", "kn2", "kn3", "kn4", "kn5",
        "kn8", "kn9",
        ]

    # all words in cst and sc texts
    print(f"[green]{'making cst text set':<40}", end="")
    cst_text_set = make_cst_text_set(ebt_books)
    print(f"{len(cst_text_set):>10,}")

    print(f"[green]{'making sc text set':<40}", end="")
    sc_text_set = make_sc_text_set(ebt_books)
    print(f"{len(sc_text_set):>10,}")
    combined_text_set = cst_text_set | sc_text_set

    # words in sandhi compounds in cst_text_set & sc_text_set
    print(f"[green]{'querying sandhi db':<40}", end="")
    sandhi_db = db_sesssion.query(Sandhi).filter(
        Sandhi.sandhi.in_(combined_text_set)).all()
    words_in_sandhi_set = make_words_in_sandhi_set(sandhi_db)
    print(f"{len(words_in_sandhi_set):>10,}")

    # all_words_set = cst_text_set + sc_text_set + words in sandhi compounds
    all_words_set = combined_text_set | words_in_sandhi_set
    print(f"[green]{'all_words_set':<40}{len(all_words_set):>10,}")

    # only include inflections which exist in all_words_set
    print(f"[green]{'creating inflections dict':<40}", end="")
    dd_db = db_sesssion.query(DerivedData).all()
    dd_dict = {}
    dd_counter = 0

    for i in dd_db:
        inflection_set = set(i.inflections_list) & all_words_set
        dd_dict[i.id] = inflection_set
        dd_counter += len(inflection_set)
    print(f"{dd_counter:>10,}")

    # a dicitonary for entries of each letter of the alphabet
    print(f"[green]{'initialising letter dict':<40}")
    letter_dict: dict = {}
    for letter in pali_alphabet:
        letter_dict[letter] = []

    # add all words which have inflections in all_words_set
    print("[green]creating entries")
    excluded = []
    word_counter = 1
    for counter, i in enumerate(dpd_db):
        inflections: set = dd_dict[i.id]
        if bool(inflections & all_words_set):
            first_letter = find_first_letter(i.pali_1)
            entry = render_ebook_entry(word_counter, i, inflections)
            letter_dict[first_letter] += [entry]
            word_counter += 1
        else:
            excluded += [i.pali_1]

        if counter % 5000 == 0:
            print(f"{counter:>10,} / {len(dpd_db):<10,} {i.pali_1}")

    # add sandhi words which are in all_words_set
    print("[green]add sandhi words")
    for counter, i in enumerate(sandhi_db):
        if bool(set(i.sandhi) & all_words_set):
            first_letter = find_first_letter(i.sandhi)
            entry = render_sandhi_entry(word_counter, i)
            letter_dict[first_letter] += [entry]
            word_counter += 1

        if counter % 5000 == 0:
            print(f"{counter:>10,} / {len(sandhi_db):<10,} {i.sandhi}")

    # save to a single file for each letter of the alphabet
    print("[green]saving entries")
    total = 0

    for counter, (letter, entries) in enumerate(letter_dict.items()):
        total += len(entries)
        entries = "".join(entries)
        xhtml = render_ebook_letter_tmpl(letter, entries)
        output_path = PTH.ebook_output_text_dir.joinpath(
            f"{counter}. {letter}.xhtml")

        with open(output_path, "w") as f:
            f.write(xhtml)

    print(f"{total:>10,} : {'included':<10}")
    print(f"{len(excluded):>10,} : {'excluded':<10}")
    toc()

# -----------------------------------------------------------------------------------------
# functions to create the various templates


def render_ebook_entry(counter: int, i: PaliWord, inflections: set) -> str:
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


def render_sandhi_entry(counter: int, i: Sandhi) -> str:
    """Render sandhi word entry."""

    sandhi = i.sandhi
    splits = "<br/>".join(i.split_list)

    return str(ebook_sandhi_templ.render(
            counter=counter,
            sandhi=sandhi,
            splits=splits))


def render_ebook_letter_tmpl(letter: str, entries: str) -> str:
    """Render all entries for a single letter."""
    return str(
        ebook_letter_tmpl.render(
            letter=letter,
            entries=entries))


if __name__ == "__main__":
    main()
