import csv
import re
import pandas as pd
import pickle
import sys

from rich import print
from json import loads
from typing import List
from os import popen
from functools import reduce

from db.get_db_session import get_db_session
from db.models import PaliWord, Sandhi, InflectionTemplates
from get_paths import get_paths
from tools.pali_sort_key import pali_sort_key
from tools.timeis import tic, toc
from tools.add_niggahitas import add_niggahitas
from tools.stardict_nu import export_words_as_stardict_zip, ifo_from_opts

sys.path.insert(1, 'tools/writemdict')
from writemdict import MDictWriter


def main():
    tic()
    """generating a grammar dictionary which shows
    all grammatical possibilities of every inflection"""

    print("[bright_yellow]grammar dicitonary")

    pth = get_paths()

    # import changed_headwords
    # import inflection tables

    # make headwords list
    db_session = get_db_session("dpd.db")

    db = db_session.query(PaliWord).all()
    db = sorted(db, key=lambda x: pali_sort_key(x.pali_1))
    headwords_list = [i.pali_1 for i in db]
    print(f"[green]all headwords{len(headwords_list):>27,}")

    nouns = ["fem", "masc", "nt", ]
    verbs = ["aor", "cond", "fut", "imp", "imperf", "opt", "perf", "pr"]
    indeclineables = ["abbrev", "abs", "ger", "ind", "inf", "prefix"]
    others = ["cs", "adj", "card", "letter", "ordin", "ordinal", "pp",
        "pron", "prp", "ptp", "root", "sandhi", "suffix", "var", "ve"]

    # modfiy parts of speech
    for i in db:
        if i.pos in nouns:
            i.pos = "noun"
        if i.pos in verbs:
            i.pos = "verb"
        if "adv" in i.grammar:
            i.pos = "adv"
        if "excl" in i.grammar:
            i.pos = "excl"
        if "prep" in i.grammar:
            i.pos = "prep"
        if "emph" in i.grammar:
            i.pos = "emph"
        if "interr" in i.grammar:
            i.pos = "interr"

    # tipitaka word set
    with open(pth.tipitaka_words_path) as f:
        reader = csv.reader(f)
        tipitaka_word_set = set([row[0] for row in reader])
        print(f"[green]all tipitaka words{len(tipitaka_word_set):>22,}")

    # sandhi words set
    sandhi_db = db_session.query(Sandhi).all()
    sandhi_split_set = set()
    for i in sandhi_db:
        sandhi_constrs = loads(i.split)
        for sandhi_constr in sandhi_constrs:
            if ("variant" not in sandhi_constr and
                    "spelling" not in sandhi_constr):
                for s in sandhi_constr.split(" + "):
                    sandhi_split_set.add(s)
    print(f"[green]all sandhi words{len(sandhi_split_set):>24,}")

    # all words set
    all_words_set = tipitaka_word_set | sandhi_split_set
    print(f"[green]all words{len(all_words_set):>31,}")

    print(f"[green]generating grammar dictionary")

    # grammar_dict structure {inflection: [(headword, pos, grammar)]}
    grammar_dict = {}
    # grammar_dict structure {inflection: "html"}
    grammar_dict_html = {}

    with open(pth.html_header_path) as f:
        html_header = f.read()

    for counter, i in enumerate(db):
        # words with ! in stem must get inflection table but no synonsyms
        if "!" in i.stem:
            i.stem = "!"
        # remove * from irregular inflections
        if i.stem == "*":
            i.stem = ""

        # process indeclinables
        if i.stem == "-":
            data_line = (i.pali_1, i.pos, "indeclineable")
            html_line = f"<tr><td><b>{i.pos}</b></td><td colspan='3'>indeclineable</td></tr>"

            # grammar_dict update
            if i.pali_clean not in grammar_dict:
                grammar_dict[i.pali_clean] = [data_line]
            else:
                if data_line not in grammar_dict[i.pali_clean]:
                    grammar_dict[i.pali_clean].append(data_line)

            # grammar_dict_html update
            if i.pali_clean not in grammar_dict_html:
                grammar_dict_html[i.pali_clean] = f"{html_header}{html_line}"
            else:
                if html_line not in grammar_dict_html[i.pali_clean]:
                    grammar_dict_html[i.pali_clean] += html_line

        elif i.stem == "!":
            pass

        elif i.pali_1 == "":
            pass

        # generate all inflections
        else:
            # get template
            template = db_session.query(
                InflectionTemplates
            ).filter(
                InflectionTemplates.pattern == i.pattern
            ).first()

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

                    if (row_number > 0 and
                        column_number % 2 == 1 and
                            column_number > 0):
                        grammar: str = [row_data[column_number+1]][0][0]

                        for inflection in cell_data:
                            if inflection != "":
                                inflected_word = f"{i.stem}{inflection}"
                                if inflected_word in all_words_set:

                                    data_line = (i.pali_1, i.pos, grammar)
                                    html_line = f"<tr>\
                                        <td><b>{i.pos}</b></td>\
                                        <td>{grammar}</td>\
                                        <td>of</td>\
                                        <td>{i.pali_clean}</td>\
                                        </tr>"

                                    # grammar_dict update
                                    if inflected_word not in grammar_dict:
                                        grammar_dict[inflected_word] = [data_line]
                                    else:
                                        if data_line not in grammar_dict[inflected_word]:
                                            grammar_dict[inflected_word].append(data_line)

                                    # grammar_dict_html update
                                    if inflected_word not in grammar_dict_html:
                                        grammar_dict_html[inflected_word] = f"{html_header}{html_line}"
                                    else:
                                        if html_line not in grammar_dict_html[inflected_word]:
                                            grammar_dict_html[inflected_word] += html_line

        if counter % 5000 == 0:
            print(f"{counter:>10,} / {len(db):<10,}{i.pali_1[:17]:>17}")

    for item in grammar_dict_html:
        grammar_dict_html[item] += "</table></div></body></html>"

    print(f"[green]saving grammar_dict pickle{len(grammar_dict):>14,}")

    with open(pth.grammar_dict_pickle_path, "wb") as f:
        pickle.dump(grammar_dict, f)

    # print(f"[green]saving html{len(grammar_dict):>29,}")
    # for k, v in grammar_dict_html.items():
    #     filepath = pth.output_html_dir.joinpath(k).with_suffix(".html")
    #     with open(filepath, "w") as f:
    #         f.write(v)

    gd_data_list, md_data_list = make_data_lists(grammar_dict_html)
    make_golden_dict(pth, gd_data_list)
    make_mdict(pth, md_data_list)
    toc()


def make_data_lists(grammar_dict_html):
    gd_data_list: List[dict] = []
    md_data_list: List[dict] = []

    for k, v in grammar_dict_html.items():
        synonyms = add_niggahitas([k])

        gd_data_list += [{
            "word": k,
            "definition_html": v,
            "definition_plain": "",
            "synonyms": synonyms
        }]

        md_data_list = [{
            "word": k,
            "definition_html": f"<h3>{k}</h3>{v}",
            "definition_plain": "",
            "synonyms": synonyms
        }]

    return gd_data_list, md_data_list


def make_golden_dict(pth, gd_data_list):
    print(f"[green]making goldendict")

    zip_path = pth.goldedict_zip_path

    ifo = ifo_from_opts({
        "bookname": "DPD Grammar",
        "author": "Bodhirasa",
        "description": "DPD Grammar",
        "website": "https://digitalpalidictionary.github.io/grammardict.html",
    })

    export_words_as_stardict_zip(gd_data_list, ifo, zip_path)

    print("[green]unipping and copying goldendict")
    popen(
        f'unzip -o {pth.goldedict_zip_path} -d "/home/bhikkhu/Documents/Golden Dict"')


def make_mdict(pth, md_data_list):
    print("[green]making mdict")

    def synonyms(all_items, item):
        all_items.append((item['word'], item['definition_html']))
        for word in item['synonyms']:
            if word != item['word']:
                all_items.append((word, f"""@@@LINK={item["word"]}"""))
        return all_items

    ifo = {
        "bookname": "DPD Grammar",
        "author": "Bodhirasa",
        "description": "DPD Grammar",
        "website": "https://digitalpalidictionary.github.io/grammardict.html",
    }

    mdict_data = reduce(synonyms, md_data_list, [])
    writer = MDictWriter(
        mdict_data, title=ifo['bookname'], description=f"<p>by {ifo['author']} </p> <p>For more infortmation, please visit <a href=\"{ifo['website']}\">{ifo['description']}</a></p>")
    outfile = open(pth.mdict_output_path, 'wb')
    writer.write(outfile)
    outfile.close()


if __name__ == "__main__":
    main()
