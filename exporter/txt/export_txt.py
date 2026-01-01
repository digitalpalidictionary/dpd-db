"""Export DPD as a plain .txt file."""

from dataclasses import dataclass
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.pali_sort_key import pali_sort_key
from tools.zip_up import zip_up_file


@dataclass
class GLobalVars:
    pr.tic()
    pr.title("exporting DPD as txt")
    pr.green("loading db")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    db_sorted = sorted(db, key=lambda x: pali_sort_key(x.lemma_1))
    db_length = len(db_sorted)
    dpd_entry_list = []
    dpd_text = ""
    debug = False  # limit to 10 000 entries
    pr.yes(db_length)


def make_word_entry(i: DpdHeadword, g: GLobalVars) -> str:
    data: list[str] = []

    # summary line
    data.append(f"{i.lemma_1}, {i.pos}. {i.meaning_combo} {i.degree_of_completion}")

    # table underneath summary
    # data.append(f"\n  Lemma: {i.lemma_clean}")
    if i.lemma_trad_clean != i.lemma_clean:
        data.append(f"\n  Traditional Lemma: {i.lemma_trad_clean}")
    data.append(f"\n  IPA: /{i.lemma_ipa}/")

    # has meaning_1, show everything
    if i.meaning_1:
        # grammar line
        data.append(f"\n  Grammar: {i.grammar}")
        if i.neg:
            data.append(f", {i.neg}")
        if i.verb:
            data.append(f", {i.verb}")
        if i.trans:
            data.append(f", {i.trans}")
        if i.plus_case:
            data.append(f" ({i.plus_case})")

        # root line
        if i.root_key:
            data.append(
                f"\n  Root: {i.family_root} {i.rt.root_group} {i.root_sign} ({i.rt.root_meaning})"
            )
            if i.rt.root_in_comps:
                data.append(f"\n  √ In Sandhi: {i.rt.root_in_comps}")

        if i.root_base:
            data.append(f"\n  Base: {i.root_base}")
        if i.construction:
            data.append(f"\n  Construction: {i.construction_line1}")
        if i.derivative and i.suffix:
            data.append(f"\n  Derivative: {i.derivative} ({i.suffix})")
        if i.phonetic:
            data.append(f"\n  Phonetic Change: {i.phonetic_txt}")
        if i.compound_type and "?" not in i.compound_type:
            data.append(f"\n  Compound: {i.compound_type}")
        if i.compound_construction:
            data.append(f" ({i.compound_construction_txt})")
        if i.antonym:
            data.append(f"\n  Antonym: {i.antonym}")
        if i.synonym:
            data.append(f"\n  Synonym: {i.synonym}")
        if i.variant:
            data.append(f"\n  Variant: {i.variant}")
        if i.notes:
            data.append(f"\n  Notes: {i.notes_txt}")
        if i.cognate:
            data.append(f"\n  English cognate: {i.cognate}")
        if i.link:
            data.append(f"\n  Web Link: {i.link_txt}")
        if i.non_ia:
            data.append(f"\n  Non IA: {i.non_ia}")

        if i.sanskrit:
            data.append(f"\n  Sanskrit: {i.sanskrit}")

        if i.root_key and i.rt.sanskrit_root:
            data.append(f"\n  Sanskrit Root: {i.rt.sanskrit_root}")
            data.append(f" {i.rt.sanskrit_root_class}")
            data.append(f" ({i.rt.sanskrit_root_meaning})")
        data.append(f"\n  ID: {i.id}")

    # no meaning_1 but pass1 or pass2, show root and construction
    elif not i.meaning_1 and i.origin in ["pass1", "pass2"]:
        # root line
        if i.root_key:
            data.append(
                f"\n  Root: {i.family_root} {i.rt.root_group} {i.root_sign} ({i.rt.root_meaning})"
            )
            if i.rt.root_in_comps:
                data.append(f"\n  √ In Sandhi: {i.rt.root_in_comps}")
        if i.root_base:
            data.append(f"\n  Base: {i.root_base}")
        if i.construction:
            data.append(f"\n  Construction: {i.construction_line1}")
        data.append(f"\n  ID: {i.id}")

    # no meaning_1 and no origin, only show the basics
    else:
        # root line
        if i.root_key:
            data.append(f"\n  Root: {i.family_root} {i.rt.root_group} ")
            if i.root_sign:
                data.append(i.root_sign)
            else:
                data.append(i.rt.root_sign)
            data.append(f" ({i.rt.root_meaning})")
            if i.rt.root_in_comps:
                data.append(f"\n  √ In Sandhi: {i.rt.root_in_comps}")
        data.append(f"\n  ID: {i.id}")

    data.append("\n")

    return "".join(data)


def export_txt(g: GLobalVars):
    pr.green_title("compiling txt")
    for counter, i in enumerate(g.db_sorted):
        if counter % 10000 == 0:
            pr.counter(counter, g.db_length, i.lemma_1)
        if counter == 10000 and g.debug:
            break
        word_entry = make_word_entry(i, g)
        g.dpd_entry_list.append(word_entry)

    g.dpd_text = "\n".join(g.dpd_entry_list)


def zip_txt_file(g: GLobalVars):
    """Zip the DPD txt file after export."""
    import time

    pr.green("zipping txt file")
    # Wait a few seconds for the file to be fully written
    time.sleep(3)

    zip_up_file(g.pth.dpd_txt_path, g.pth.dpd_txt_zip_path)
    pr.yes("ok")
    pr.info(f"saved to {g.pth.dpd_txt_zip_path}")


def save_txt(g: GLobalVars):
    pr.green("saving txt")
    g.pth.dpd_txt_path.write_text(g.dpd_text)
    pr.yes(len(g.dpd_entry_list))


def main():
    g = GLobalVars()
    export_txt(g)
    save_txt(g)
    zip_txt_file(g)
    pr.toc()


if __name__ == "__main__":
    main()
