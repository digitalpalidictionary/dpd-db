from db.get_db_session import get_db_session
from db.models import PaliWord


def copy_word_from_db(sg, values, window):
    db_session = get_db_session("dpd.db")
    i = db_session.query(
        PaliWord
    ).filter(
        PaliWord.pali_1 == values["word_to_copy"]
    ).first()

    if i is None:
        window["messages"].update(
            "{values['word_to_copy']}' not found in db", text_color="red"
        ),

    if i is not None:

        # window["id"].update(i.id)
        # window["user_id"].update(i.user_id)
        # window["pali_1"].update(i.pali_1)
        window["pali_2"].update(i.pali_2)
        window["pos"].update(i.pos)
        window["grammar"].update(i.grammar)
        window["derived_from"].update(i.derived_from)
        window["neg"].update(i.neg)
        window["verb"].update(i.verb)
        window["trans"].update(i.trans)
        window["plus_case"].update(i.plus_case)
        window["meaning_1"].update(i.meaning_1)
        window["meaning_lit"].update(i.meaning_lit)
        window["meaning_2"].update(i.meaning_2)
        window["non_ia"].update(i.non_ia)
        window["sanskrit"].update(i.sanskrit)
        window["root_key"].update(i.root_key)
        window["root_sign"].update(i.root_sign)
        window["root_base"].update(i.root_base)
        window["family_root"].update(i.family_root)
        window["family_word"].update(i.family_word)
        window["family_compound"].update(i.family_compound)
        window["family_set"].update(i.family_set)
        window["construction"].update(i.construction)
        window["derivative"].update(i.derivative)
        window["suffix"].update(i.suffix)
        window["phonetic"].update(i.phonetic)
        window["compound_type"].update(i.compound_type)
        window["compound_construction"].update(i.compound_construction)
        window["non_root_in_comps"].update(i.non_root_in_comps)
        window["source_1"].update(i.source_1)
        window["sutta_1"].update(i.sutta_1)
        window["example_1"].update(i.example_1)
        window["source_2"].update(i.source_2)
        window["sutta_2"].update(i.sutta_2)
        window["example_2"].update(i.example_2)
        window["antonym"].update(i.antonym)
        window["synonym"].update(i.synonym)
        window["variant"].update(i.variant)
        window["commentary"].update(i.commentary)
        window["notes"].update(i.notes)
        window["cognate"].update(i.cognate)
        window["link"].update(i.link)
        window["origin"].update(i.origin)
        window["stem"].update(i.stem)
        window["pattern"].update(i.pattern)
        window["word_to_copy"].update("")
        print(values)
    return values, window
