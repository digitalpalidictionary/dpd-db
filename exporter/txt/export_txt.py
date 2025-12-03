"""Export DPD as a plain .txt file."""

from dataclasses import dataclass
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.pali_sort_key import pali_sort_key
import re

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
    pr.yes(db_length)


def make_word_entry(i: DpdHeadword, g: GLobalVars) -> str:
    data: list[str] = []
    data.append(i.lemma_1)

    # has meaning_1, show everything
    if i.meaning_1:
        if i.grammar:
            data.append(f", {i.grammar}")
        if i.neg:
            data.append(f", {i.neg}")
        if i.verb:
            data.append(f", {i.verb}")
        if i.trans:
            data.append(f", {i.trans}")
        if i.plus_case:
            data.append(f" ({i.plus_case})")
        data.append(f": {i.meaning_1}")
        if i.meaning_lit:
            data.append(f"; lit. {i.meaning_lit}")
        if i.root_key:
            data.append(f". root: {i.family_root} {i.rt.root_group} {i.root_sign} ({i.rt.root_meaning})")
        if i.root_base:
            data.append(f". base: {i.root_base}")
        if i.construction:
            data.append(f". construction: {i.construction_line1}")
        if i.phonetic:
            data.append(f". phonetic change: {i.phonetic_txt}")
        if i.derivative and i.suffix:
            data.append(f". derivative: {i.derivative} ({i.suffix})")
        if i.compound_type:
            data.append(f". compound: {i.compound_type}")
        if i.compound_construction:
            data.append(f" ({i.compound_construction_txt})")
        if i.antonym:
            data.append(f". antonym: {i.antonym}")
        if i.synonym:
            data.append(f". synonym: {i.synonym}")
        if i.variant:
            data.append(f". variant: {i.variant}")
        if i.notes:
            data.append(f". notes: {i.notes_txt}")
        if i.non_ia:
            data.append(f". non-IA: {i.non_ia}")
        if i.sanskrit:
            data.append(f". Sanskrit: {i.sanskrit}")
        if i.cognate:
            data.append(f". English cognate: {i.cognate}")
    
    # no meaning_1 but pass1 or pass2, show root and construction
    elif not i.meaning_1 and i.origin in ["pass1", "pass2"]:
        data.append(f", {i.pos}")
        data.append(f": {i.meaning_2}")
        if i.meaning_lit:
            data.append(f"; lit. {i.meaning_lit}")
        if i.root_key:
            data.append(f". root: {i.family_root} {i.rt.root_group} {i.root_sign} ({i.rt.root_meaning})")
        if i.root_base:
            data.append(f". base: {i.root_base}")
        if i.construction:
            data.append(f". construction: {i.construction_line1}")
    
    # no meaning_1 and no origin, only show the basics
    else:
        data.append(f", {i.pos}")
        data.append(f": {i.meaning_2}")
        if i.meaning_lit:
            data.append(f"; lit. {i.meaning_lit}")
        if i.root_key:
            data.append(f". root: {i.family_root} {i.rt.root_group} {i.root_sign} ({i.rt.root_meaning})")
    
    data.append(f" {i.degree_of_completion}")

    return "".join(data)


def export_txt(g: GLobalVars):
    pr.green_title("exporting txt")
    for counter, i in enumerate(g.db_sorted):
        if counter % 10000 == 0:
            pr.counter(counter, g.db_length, i.lemma_1)
        word_entry = make_word_entry(i, g)
        g.dpd_entry_list.append(word_entry)

    g.dpd_text = "\n".join(g.dpd_entry_list)


def save_txt(g: GLobalVars):
    pr.green("saving txt")
    g.pth.dpd_txt_path.write_text(g.dpd_text)
    pr.yes(len(g.dpd_entry_list))

def main():
    g = GLobalVars()
    export_txt(g)
    save_txt(g)
    pr.toc()

if __name__ == '__main__':
    main()