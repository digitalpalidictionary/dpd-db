from rich import print
from sqlalchemy import desc, update

from db.get_db_session import get_db_session
from db.models import PaliWord

db_session = get_db_session("dpd.db")


class Word:
    def __init__(self, pali_1, pali_2, pos, grammar, derived_from, neg, verb, trans, plus_case, meaning_1, meaning_lit, meaning_2, non_ia, sanskrit, root_key, root_sign, root_base, family_root, family_word, family_compound, family_set, construction, derivative, suffix, phonetic, compound_type, compound_construction, non_root_in_comps, source_1, sutta_1, example_1, source_2, sutta_2, example_2, antonym, synonym, variant, commentary, notes, cognate, link, origin, stem, pattern):
        self.pali_1: str
        self.pali_2: str
        self.pos: str
        self.grammar: str
        self.derived_from: str
        self.neg: str
        self.verb: str
        self.trans: str
        self.plus_case: str
        self.meaning_1: str
        self.meaning_lit: str
        self.meaning_2: str
        self.non_ia: str
        self.sanskrit: str
        self.root_key: str
        self.root_sign: str
        self.root_base: str
        self.family_root: str
        self.family_word: str
        self.family_compound: str
        self.family_set: str
        self.construction: str
        self.derivative: str
        self.suffix: str
        self.phonetic: str
        self.compound_type: str
        self.compound_construction: str
        self.non_root_in_comps: str
        self.source_1: str
        self.sutta_1: str
        self.example_1: str
        self.source_2: str
        self.sutta_2: str
        self.example_2: str
        self.antonym: str
        self.synonym: str
        self.variant: str
        self.commentary: str
        self.notes: str
        self.cognate: str
        self.link: str
        self.origin: str
        self.stem: str
        self.pattern: str


def copy_compound_from_db(sg, values, window):

    i = db_session.query(
        PaliWord
    ).filter(
        PaliWord.pali_1 == values["compound_to_copy"]
    ).first()

    if i is None:
        sg.popup(
            f"'{values['compound_to_copy']}' not found in db",
            title="Error"
        ),

    if i is not None:

        window["id"].update(i.id)
        window["user_id"].update(i.user_id)
        window["pali_1"].update(i.pali_1)
        window["pali_2"].update(i.pali_2)
        window["pos"].update(i.pos)
        window["grammar"].update(i.grammar)
        # window["derived_from"].update(i.derived_from)
        window["neg"].update(i.neg)
        # window["verb"].update(i.verb)
        # window["trans"].update(i.trans)
        window["plus_case"].update(i.plus_case)
        window["meaning_1"].update(i.meaning_1)
        window["meaning_lit"].update(i.meaning_lit)
        # window["meaning_2"].update(i.meaning_2)
        # window["non_ia"].update(i.non_ia)
        # window["sanskrit"].update(i.sanskrit)
        # window["root_key"].update(i.root_key)
        # window["root_sign"].update(i.root_sign)
        # window["root_base"].update(i.root_base)
        # window["family_root"].update(i.family_root)
        # window["family_word"].update(i.family_word)
        window["family_compound"].update(i.family_compound)
        window["family_set"].update(i.family_set)
        window["construction"].update(i.construction)
        # window["derivative"].update(i.derivative)
        # window["suffix"].update(i.suffix)
        # window["phonetic"].update(i.phonetic)
        window["compound_type"].update(i.compound_type)
        window["compound_construction"].update(i.compound_construction)
        # window["non_root_in_comps"].update(i.non_root_in_comps)
        # window["source_1"].update(i.source_1)
        # window["sutta_1"].update(i.sutta_1)
        # window["example_1"].update(i.example_1)
        # window["source_2"].update(i.source_2)
        # window["sutta_2"].update(i.sutta_2)
        # window["example_2"].update(i.example_2)
        window["antonym"].update(i.antonym)
        window["synonym"].update(i.synonym)
        window["variant"].update(i.variant)
        window["commentary"].update(i.commentary)
        # window["notes"].update(i.notes)
        # window["cognate"].update(i.cognate)
        # window["link"].update(i.link)
        window["origin"].update(i.origin)
        window["stem"].update(i.stem)
        window["pattern"].update(i.pattern)
        window["compound_to_copy"].update("")
        print(values)
    return values, window


def grammar_length():
    x = db_session.query(PaliWord).all()
    grammar_length = 0
    maxx = 0
    for counter, i in enumerate(x):
        grammar_length += len(i.grammar)
        if len(i.grammar) > maxx:
            maxx = len(i.grammar)
    average = grammar_length / counter
    print(f"{average=}")
    print(f"{maxx=}")


def print_pos_list() -> list:
    pos_db = db_session.query(
        PaliWord.pos
    ).group_by(
        PaliWord.pos
    ).all()
    pos_list = sorted([i.pos for i in pos_db])
    return print(pos_list, end=" ")


# print_pos_list()

def get_next_ids():
    # get next id
    last_id = db_session.query(PaliWord.id).order_by(
        desc(PaliWord.id)).first()[0]
    next_id = last_id+1

    # get next user id
    last_user_id = db_session.query(PaliWord.user_id).order_by(
        desc(PaliWord.user_id)).first()[0]
    next_user_id = last_user_id+1
    return next_id, next_user_id


def values_to_pali_word(values):
    return PaliWord(
        id=values["id"],
        user_id=int(values["user_id"]),
        pali_1=values["pali_1"],
        pali_2=values["pali_2"],
        pos=values["pos"],
        grammar=values["grammar"],
        neg=values["neg"],
        plus_case=values["plus_case"],
        meaning_1=values["meaning_1"],
        meaning_lit=values["meaning_lit"],
        family_compound=values["family_compound"],
        family_set=values["family_set"],
        construction=values["construction"],
        compound_type=values["compound_type"],
        compound_construction=values["compound_construction"],
        antonym=values["antonym"],
        synonym=values["synonym"],
        variant=values["variant"],
        commentary=values["commentary"],
        stem=values["stem"],
        pattern=values["pattern"],
        origin=values["origin"]
    )


def add_word_to_db(values: dict, sg) -> None:
    word_to_add = values_to_pali_word(values)

    exists = db_session.query(
        PaliWord
        ).filter(
            PaliWord.pali_1 == values["pali_1"]
        ).first()

    if exists:
        sg.popup(
            f"""'{values['pali_1']}' already in db.
Use Update instead""",
            title="Error")

    else:
        try:
            db_session.add(word_to_add)
            db_session.commit()
            sg.popup(
                f"'{values['pali_1']}' added to db",
                title="Success!"
                )
        except Exception as e:
            sg.popup(
                f"{str(e)}",
                title="Error"
                )


def update_word_in_db(values: dict, sg) -> None:
    # dict_to_add = [values_to_dict(values)]

    word = db_session.query(
        PaliWord
        ).filter(
            PaliWord.pali_1 == values["pali_1"]
        ).first()

    if not word:
        sg.popup(
            f"""'{values['pali_1']}' not in db.
Use Add instead""",
            title="Error")

    else:
        print(word.id)
        word.id = int(values["id"])
        word.user_id = int(values["user_id"])
        word.pali_1 = values["pali_1"]
        word.pali_2 = values["pali_2"]
        word.pos = values["pos"]
        word.grammar = values["grammar"]
        word.neg = values["neg"]
        word.plus_case = values["plus_case"]
        word.meaning_1 = values["meaning_1"]
        word.meaning_lit = values["meaning_lit"]
        word.family_compound = values["family_compound"]
        word.family_set = values["family_set"]
        word.construction = values["construction"]
        word.compound_type = values["compound_type"]
        word.compound_construction = values["compound_construction"]
        word.antonym = values["antonym"]
        word.synonym = values["synonym"]
        word.variant = values["variant"]
        word.commentary = values["commentary"]
        word.stem = values["stem"]
        word.pattern = values["pattern"]
        word.origin = values["origin"]

        try:
            db_session.commit()
            sg.popup(
                f"'{values['pali_1']}' updated in db",
                title="Success!"
            )
        except Exception as e:
            sg.popup(
                f"{str(e)}",
                title="Error"
            )
