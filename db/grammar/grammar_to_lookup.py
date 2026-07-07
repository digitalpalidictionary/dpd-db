#!/usr/bin/env python3

"""Compile data of all grammatical possibilities of every inflected word-form and save it to lookup table of db."""

from json import loads

from db.db_helpers import get_db_session
from db.models import DpdHeadword, InflectionTemplates
from tools.all_tipitaka_words import make_all_tipitaka_word_set
from tools.configger import config_read
from tools.deconstructed_words import make_words_in_deconstructions
from tools.lookup_sync import sync_lookup_column
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class GlobalVars:
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db = self.load_db()

        # types of words
        self.nouns = [
            "fem",
            "masc",
            "nt",
        ]
        self.verbs = ["aor", "cond", "fut", "imp", "imperf", "opt", "perf", "pr"]
        self.all_words_set: set[str]

        # the grammar data
        self.grammar_data: dict[str, list[tuple[str, str, str]]]

    def load_db(self) -> list[DpdHeadword]:
        db = self.db_session.query(DpdHeadword).all()
        return sorted(db, key=lambda x: pali_sort_key(x.lemma_1))


def main() -> None:
    pr.tic()
    pr.yellow_title("exporting grammar data")
    if config_read("generate", "grammar", "yes") == "no":
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    g = GlobalVars()

    pos_override = modify_pos(g.db, g.nouns, g.verbs)
    make_sets_of_words(g)
    generate_grammar_data(g, pos_override)
    add_to_lookup_table(g)
    pr.toc()


def modify_pos(
    db: list[DpdHeadword],
    nouns: list[str],
    verbs: list[str],
) -> dict[int, str]:
    """Return a mapping of headword id → overridden pos for grammar categorisation.

    Never mutates the ORM objects so the session stays clean.
    """
    pos_override: dict[int, str] = {}
    for i in db:
        pos = i.pos
        if pos in nouns:
            pos = "noun"
        if pos in verbs:
            pos = "verb"
        if "adv" in i.grammar and i.pos != "sandhi":
            pos = "adv"
        if "excl" in i.grammar:
            pos = "excl"
        if "prep" in i.grammar:
            pos = "prep"
        if "emph" in i.grammar:
            pos = "emph"
        if "interr" in i.grammar:
            pos = "interr"
        if pos != i.pos:
            pos_override[i.id] = pos
    return pos_override


def make_sets_of_words(g: GlobalVars) -> None:
    """Make the set of all words to be used,
    all words in the tipitaka + all the words in deconstructed compounds"""

    # tipitaka word set
    pr.green_tmr("all tipitaka words")
    tipitaka_word_set = make_all_tipitaka_word_set()
    pr.yes(len(tipitaka_word_set))

    # word in deconstructed compounds
    pr.green_tmr("all words in deconstructions")
    words_in_deconstructions_set = make_words_in_deconstructions(g.db_session)
    pr.yes(len(words_in_deconstructions_set))

    # all words set
    pr.green_tmr("all words set")
    g.all_words_set = tipitaka_word_set | words_in_deconstructions_set
    pr.yes(len(g.all_words_set))


def generate_grammar_data(g: GlobalVars, pos_override: dict[int, str]) -> None:
    pr.green_title("generating grammar data")

    # grammar_data is pure data {inflection: [(headword, pos, grammar)]}

    grammar_data: dict[str, list[tuple[str, str, str]]] = {}

    templates = {t.pattern: t for t in g.db_session.query(InflectionTemplates).all()}

    # process the inflections of each word in DpdHeadword
    for counter, i in enumerate(g.db):
        # words with ! in the stem are inflected forms
        # and will get dealt with under the main headwords
        if "!" in i.stem:
            continue

        # words with '*' in stem are irregular inflections, use "" for clean processing.
        stem = "" if i.stem == "*" else i.stem

        # process indeclinables
        if stem == "-":
            continue

        # all other words need an inflection table generated
        # to find out their grammatical category, i.e. masc nom sg
        template = templates.get(i.pattern)
        if template is not None:
            template_data = loads(template.data)

            # data is a nest of lists
            # list[] table
            # list[[]] row
            # list[[[]]] cell
            # row 0 is the top header
            # column 0 is the grammar header
            # odd rows > 0 are inflections
            # even rows > 0 are grammar info

            for row_number, row_data in enumerate(template_data):
                for column_number, cell_data in enumerate(row_data):
                    if (
                        row_number > 0  #   skip the top header
                        and column_number > 0  #   skip the side header
                        and column_number % 2 == 1  #   skip even = grammar info
                        and row_data[0][0] != "in comps"  #   skip this row
                    ):
                        grammar = row_data[column_number + 1][0]

                        for inflection in cell_data:
                            if inflection:
                                inflected_word = f"{stem}{inflection}"
                                if inflected_word in g.all_words_set:
                                    data_line = (
                                        i.lemma_clean,
                                        pos_override.get(i.id, i.pos),
                                        grammar,
                                    )
                                    if inflected_word not in grammar_data:
                                        grammar_data[inflected_word] = [data_line]
                                    elif data_line not in grammar_data[inflected_word]:
                                        grammar_data[inflected_word].append(data_line)

        if counter % 5000 == 0:
            pr.counter(counter, len(g.db), i.lemma_1)

    pr.green_tmr("compiling grammar data")
    g.grammar_data = grammar_data
    pr.yes(len(g.grammar_data))


def add_to_lookup_table(g: GlobalVars) -> None:
    """Add the grammar data items to the Lookup table."""

    pr.green_tmr("saving to Lookup table")
    sync_lookup_column(g.db_session, "grammar", g.grammar_data, use_raw_sql=True)
    pr.yes("ok")


if __name__ == "__main__":
    main()
