#!/usr/bin/env python3

"""Compile data of all grammatical possibilities of every inflected word-form and save it to lookup table of db."""

from json import loads

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from db.models import InflectionTemplates
from db.models import Lookup

from tools.all_tipitaka_words import make_all_tipitaka_word_set
from tools.deconstructed_words import make_words_in_deconstructions
from tools.lookup_is_another_value import is_another_value
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.update_test_add import update_test_add


class ProgData:
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
        self.all_words_set: set

        # the grammar data
        self.grammar_data: dict[str, list[tuple[str, str, str]]]

    def load_db(self):
        db = self.db_session.query(DpdHeadword).all()
        return sorted(db, key=lambda x: pali_sort_key(x.lemma_1))

    def close_db(self):
        self.db_session.close()

    def commit_db(self):
        self.db_session.commit()


def main():
    pr.tic()
    pr.title("exporting grammar data")

    g = ProgData()

    modify_pos(g)
    make_sets_of_words(g)
    generate_grammar_data(g)

    # dont commit the changes into the db
    g.close_db()
    g.load_db()

    add_to_lookup_table(g)
    pr.toc()


def modify_pos(g: ProgData):
    """Modify parts of speech into general categories."""

    # modify parts of speech
    for i in g.db:
        if i.pos in g.nouns:
            i.pos = "noun"
        if i.pos in g.verbs:
            i.pos = "verb"
        if "adv" in i.grammar and i.pos != "sandhi":
            i.pos = "adv"
        if "excl" in i.grammar:
            i.pos = "excl"
        if "prep" in i.grammar:
            i.pos = "prep"
        if "emph" in i.grammar:
            i.pos = "emph"
        if "interr" in i.grammar:
            i.pos = "interr"


def make_sets_of_words(g: ProgData):
    """Make the set of all words to be used,
    all words in the tipitaka + all the words in deconstructed compounds"""

    # tipitaka word set
    pr.green("all tipitaka words")
    tipitaka_word_set = make_all_tipitaka_word_set()
    pr.yes(len(tipitaka_word_set))

    # word in deconstructed compounds
    pr.green("all words in deconstructions")
    words_in_deconstructions_set = make_words_in_deconstructions(g.db_session)
    pr.yes(len(words_in_deconstructions_set))

    # all words set
    pr.green("all words set")
    g.all_words_set = tipitaka_word_set | words_in_deconstructions_set
    pr.yes(len(g.all_words_set))





def generate_grammar_data(g: ProgData):
    pr.green_title("generating grammar data")

    # grammar_data is pure data {inflection: [(headword, pos, grammar)]}

    grammar_data = {}

    # process the inflections of each word in DpdHeadword
    for counter, i in enumerate(g.db):
        # words with ! in the stem are inflected forms
        # and wil get dealt with under the main headwords
        if "!" in i.stem:
            pass

        # words with '*' in stem are irregular inflections, remove the * for clean processing.
        if i.stem == "*":
            i.stem = ""

        # process indeclinables
        if i.stem == "-":
            continue

        # all other words need an inflection table generated
        # to find out their grammatical category, i.e. masc nom sg
        else:
            # get template
            template = (
                g.db_session.query(InflectionTemplates)
                .filter(InflectionTemplates.pattern == i.pattern)
                .first()
            )

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
                            and column_number % 2
                            == 1  #   skip even numbers = grammar info
                            and row_data[0][0] != "in comps"  #   skip this row
                        ):
                            grammar: str = [row_data[column_number + 1]][0][0]

                            for inflection in cell_data:
                                if inflection:
                                    inflected_word = f"{i.stem}{inflection}"
                                    if inflected_word in g.all_words_set:
                                        data_line = (i.lemma_clean, i.pos, grammar)
                                        html_line = "<tr>"
                                        html_line += f"<td><b>{i.pos}</b></td>"
                                        # get grammatical_categories from grammar
                                        grammatical_categories = []
                                        if grammar.startswith("reflx"):
                                            grammatical_categories.append(
                                                grammar.split()[0]
                                                + " "
                                                + grammar.split()[1]
                                            )
                                            grammatical_categories += grammar.split()[
                                                2:
                                            ]
                                            for (
                                                grammatical_category
                                            ) in grammatical_categories:
                                                html_line += (
                                                    f"<td>{grammatical_category}</td>"
                                                )
                                        elif grammar.startswith("in comps"):
                                            html_line += (
                                                f"<td colspan='3'>{grammar}</td>"
                                            )
                                        else:
                                            grammatical_categories = grammar.split()
                                            # adding empty values if there are less than 3
                                            while len(grammatical_categories) < 3:
                                                grammatical_categories.append("")
                                            for (
                                                grammatical_category
                                            ) in grammatical_categories:
                                                html_line += (
                                                    f"<td>{grammatical_category}</td>"
                                                )
                                        html_line += "<td>of</td>"
                                        html_line += f"<td>{i.lemma_clean}</td>"
                                        html_line += "</tr>"

                                        if inflected_word not in grammar_data:
                                            grammar_data[inflected_word] = [data_line]
                                        else:
                                            if (
                                                data_line
                                                not in grammar_data[inflected_word]
                                            ):
                                                grammar_data[inflected_word].append(
                                                    data_line
                                                )

        if counter % 5000 == 0:
            pr.counter(counter, len(g.db), i.lemma_1)



    g.grammar_data = grammar_data

    pr.yes(len(g.grammar_data))



def add_to_lookup_table(g: ProgData):
    """Add the grammar data items to the Lookup table."""

    pr.green("saving to Lookup table")

    lookup_table = g.db_session.query(Lookup).all()
    results = update_test_add(lookup_table, g.grammar_data)
    update_set, test_set, add_set = results

    # update test add
    for i in lookup_table:
        if i.lookup_key in update_set:
            i.grammar_pack(g.grammar_data[i.lookup_key])
        elif i.lookup_key in test_set:
            if is_another_value(i, "grammar"):
                i.grammar = ""
            else:
                g.db_session.delete(i)

    g.commit_db()

    # add
    add_to_db = []
    for inflection, grammar_data in g.grammar_data.items():
        if inflection in add_set:
            add_me = Lookup()
            add_me.lookup_key = inflection
            add_me.grammar_pack(grammar_data)
            add_to_db.append(add_me)

    g.db_session.add_all(add_to_db)
    g.commit_db()

    pr.yes("ok")



if __name__ == "__main__":
    main()
