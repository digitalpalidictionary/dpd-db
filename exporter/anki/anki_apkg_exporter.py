#!/usr/bin/env python3

"""Export the DPD Vocab deck to an .apkg for public distribution."""

from pathlib import Path

import genanki

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr

TEMPLATES_DIR = Path("exporter/anki/templates")

MODEL_ID = 1_607_392_319  # stable arbitrary id
DECK_ID = 1_891_213_047  # stable arbitrary id

FIELDS = [
    "id",
    "lemma_1",
    "lemma_2",
    "fin",
    "pos",
    "grammar",
    "derived_from",
    "neg",
    "verb",
    "trans",
    "plus_case",
    "meaning_1",
    "meaning_lit",
    "non_ia",
    "sanskrit",
    "root_key",
    "root_sign",
    "root_base",
    "sanskrit_root",
    "sanskrit_root_meaning",
    "sanskrit_root_class",
    "root_meaning",
    "root_in_comps",
    "root_has_verb",
    "root_group",
    "family_root",
    "family_word",
    "family_compound",
    "family_idioms",
    "construction",
    "derivative",
    "suffix",
    "phonetic",
    "compound_type",
    "compound_construction",
    "non_root_in_comps",
    "source_1",
    "sutta_1",
    "example_1",
    "source_2",
    "sutta_2",
    "example_2",
    "antonym",
    "synonym",
    "var_phonetic",
    "var_text",
    "variant",
    "commentary",
    "notes",
    "cognate",
    "family_set",
    "link",
    "stem",
    "pattern",
    "meaning_2",
    "origin",
    "pic",
    "notez",
]


def make_model() -> genanki.Model:
    front = (TEMPLATES_DIR / "front.html").read_text(encoding="utf-8")
    back = (TEMPLATES_DIR / "public_back.html").read_text(encoding="utf-8")
    styling = (TEMPLATES_DIR / "public_styling.html").read_text(encoding="utf-8")

    return genanki.Model(
        MODEL_ID,
        "DPD",
        fields=[{"name": f} for f in FIELDS],
        templates=[{"name": "Card 1", "qfmt": front, "afmt": back}],
        css=styling,
    )


def make_note_fields(i: DpdHeadword) -> list[str]:
    if i.meaning_1 and i.sutta_1:
        fin = "√√"
    elif i.meaning_1:
        fin = "√"
    else:
        fin = ""

    return [
        str(i.id),
        str(i.lemma_1),
        str(i.lemma_2),
        fin,
        str(i.pos),
        str(i.grammar),
        str(i.derived_from),
        str(i.neg),
        str(i.verb),
        str(i.trans),
        str(i.plus_case),
        str(i.meaning_1),
        str(i.meaning_lit),
        str(i.non_ia),
        str(i.sanskrit),
        str(i.root_clean),
        str(i.root_sign),
        str(i.root_base),
        str(i.rt.sanskrit_root) if i.root_key else "",
        str(i.rt.sanskrit_root_meaning) if i.root_key else "",
        str(i.rt.sanskrit_root_class) if i.root_key else "",
        str(i.rt.root_meaning) if i.root_key else "",
        str(i.rt.root_in_comps) if i.root_key else "",
        str(i.rt.root_has_verb) if i.root_key else "",
        str(i.rt.root_group) if i.root_key else "",
        str(i.family_root),
        str(i.family_word),
        str(i.family_compound),
        str(i.family_idioms),
        str(i.construction).replace("\n", "<br>"),
        str(i.derivative),
        str(i.suffix),
        str(i.phonetic).replace("\n", "<br>"),
        str(i.compound_type),
        str(i.compound_construction),
        str(i.non_root_in_comps),
        str(i.source_1),
        str(i.sutta_1).replace("\n", "<br>"),
        str(i.example_1).replace("\n", "<br>"),
        str(i.source_2),
        str(i.sutta_2).replace("\n", "<br>"),
        str(i.example_2).replace("\n", "<br>"),
        str(i.antonym),
        str(i.synonym),
        str(i.var_phonetic),
        str(i.var_text),
        str(i.variant),
        str(i.commentary).replace("\n", "<br>"),
        str(i.notes).replace("\n", "<br>"),
        str(i.cognate),
        str(i.family_set),
        str(i.link).replace("\n", "<br>"),
        str(i.stem),
        str(i.pattern),
        str(i.meaning_2),
        str(i.origin),
        "",  # pic
        "",  # notez
    ]


def main() -> None:
    pr.tic()
    pr.yellow_title("building dpd-anki.apkg")

    pth = ProjectPaths()

    pr.green_tmr("querying db")
    db_session = get_db_session(pth.dpd_db_path)
    vocab = (
        db_session.query(DpdHeadword)
        .filter(
            DpdHeadword.meaning_1 != "",
            DpdHeadword.source_1 != "",
            DpdHeadword.source_1 != "-",
            ~DpdHeadword.meaning_1.startswith("(gram)"),
        )
        .order_by(DpdHeadword.ebt_count.desc())
        .all()
    )
    pr.yes(len(vocab))

    pr.green_tmr("building notes")
    model = make_model()
    deck = genanki.Deck(DECK_ID, "DPD")

    for i in vocab:
        note = genanki.Note(
            model=model,
            fields=make_note_fields(i),
            guid=str(i.id),
        )
        deck.add_note(note)
    pr.yes(len(vocab))

    pr.green_tmr("writing .apkg")
    genanki.Package(deck).write_to_file(str(pth.dpd_anki_apkg_path))
    pr.yes("ok")

    pr.toc()


if __name__ == "__main__":
    main()
