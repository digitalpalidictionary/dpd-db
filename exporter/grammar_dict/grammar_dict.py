#!/usr/bin/env python3

"""Compile HTML table of all grammatical possibilities of
every inflected wordform."""

import csv
import pickle

from css_html_js_minify import css_minify, js_minify
from json import loads
from mako.template import Template
from pathlib import Path
from rich import print
from subprocess import Popen, PIPE
from typing import List

from db.get_db_session import get_db_session
from db.models import DpdHeadwords
from db.models import InflectionTemplates
from db.models import Lookup

from tools.configger import config_test
from tools.deconstructed_words import make_words_in_deconstructions
from tools.goldendict_path import goldedict_path
from tools.lookup_is_another_value import is_another_value
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.tic_toc import tic, toc
from tools.update_test_add import update_test_add


class ProgData():
    def __init__(self) -> None:
        self.make_mdct: bool
        self.copy_unzip: bool

        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db = self.load_db()
        self.headwords_list: list[str] = [i.lemma_1 for i in self.db]

        # types of words
        self.nouns = ["fem", "masc", "nt", ]
        self.verbs = ["aor", "cond", "fut", "imp", "imperf", "opt", "perf", "pr"]
        self.all_words_set: set

        # the grammar dictionries
        self.grammar_dict: dict[str, tuple[str, str, str]]
        self.grammar_dict_table: dict[str, tuple[str, str, str]]
        self.grammar_dict_html: dict[str, tuple[str, str, str]]

        # goldendict and mdict data_list
        self.gd_data_list: list

        # book info
        self.bookname: str
        self.author: str
        self.description: str 
        self.website: str

    def load_db(self):
        db = self.db_session.query(DpdHeadwords).all()
        return sorted(db, key=lambda x: pali_sort_key(x.lemma_1))
    
    def close_db(self):
        self.db_session.close()
    
    def commit_db(self):
        self.db_session.commit()


def main():
    tic()
    print("[bright_yellow]grammar dictionary")
    pd = ProgData()
    continue_ok = config_tests(pd)
    
    if continue_ok:
        modify_pos(pd)
        make_sets_of_words(pd)
        generate_grammar_dict(pd)
        
        # dont commit the changes into the db
        pd.close_db()
        pd.load_db()
        
        save_pickle_and_tsv(pd)
        add_to_lookup_table(pd)
        make_data_lists(pd)
        make_goldendict(pd)
        if pd.copy_unzip:
            unzip_and_copy_goldendict(pd)
        if pd.make_mdct:
            make_mdict(pd)

    toc()


def config_tests(pd) -> bool:
    """
    Check config.ini 
    - whether to continue
    - set program variables.
    """
    print("[green]running config tests")

    if config_test("exporter", "make_grammar", "no"):
        print("generating is disabled in the config")
        return False

    if config_test("dictionary", "make_mdict", "yes"):
        pd.make_mdct = True
    else:
        pd.make_mdct = False

    if config_test("goldendict", "copy_unzip", "yes"):
        pd.copy_unzip = True
    else:
        pd.copy_unzip = False

    return True


def modify_pos(pd):
    """Modify parts of speech into general categories."""

    # modfiy parts of speech
    for i in pd.db:
        if i.pos in pd.nouns:
            i.pos = "noun"
        if i.pos in pd.verbs:
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


def make_sets_of_words(pd):
    """Make the set of all words to be used,
    all words in the tipitaka + all the words in deconstructed compounds"""

    # tipitaka word set
    print(f"[green]{'all tipitaka words':<40}", end="")
    with open(pd.pth.tipitaka_word_count_path) as f:
        reader = csv.reader(f, delimiter="\t")
        tipitaka_word_set = set([row[0] for row in reader])
    print(f"{len(tipitaka_word_set):>10,}")

    # word in deconstucted compounds
    print(f"[green]{'all words in deconstructions':<40}", end="")
    words_in_deconstructions_set = make_words_in_deconstructions(pd.db_session)
    print(f"{len(words_in_deconstructions_set):>10,}")

    # all words set
    print(f"[green]{'all words set':<40}", end="")
    pd.all_words_set = tipitaka_word_set | words_in_deconstructions_set
    print(f"{len(pd.all_words_set):>10,}")


def render_header_templ(
        __pth__: ProjectPaths,
        css: str,
        js: str,
        header_templ: Template
) -> str:
    """render the html header with css and js"""

    return str(header_templ.render(css=css, js=js))


def generate_grammar_dict(pd):
    print("[green]generating grammar dictionary")

    # three grammar dicts will be generated here at the same time. 
    # 1. grammar_dict is pure data {inflection: [(headword, pos, grammar)]}
    # 2. grammar_dict_table is just an html table {inflection: "html"}
    # 3. grammar_dict_html is full html page with header, style etc. {inflection: "html"}

    grammar_dict = {}
    grammar_dict_table = {}
    grammar_dict_html = {}

    # find the css for grammar_dict_html
    with open(pd.pth.grammar_css_path) as f:
        grammar_css = f.read()
    grammar_css = css_minify(grammar_css)

    # find the js table sorter for grammar_dict_html
    with open(pd.pth.sorter_js_path) as f:
        sorter_js = f.read()
    sorter_js = js_minify(sorter_js)

    # create the header from a template
    header_templ = Template(filename=str(pd.pth.header_grammar_dict_templ_path))
    html_header = render_header_templ(
        pd.pth, css=grammar_css, js=sorter_js, header_templ=header_templ)
    html_header += "<body><div class='grammar_dict'><table class='grammar_dict'>"
    html_header += "<thead><tr><th id='col1'>pos ⇅</th><th id='col2'>⇅</th><th id='col3'>⇅</th><th id='col4'>⇅</th><th id='col5'></th><th id='col6'>word ⇅</th></tr></thead><tbody>"
    
    html_table_header = "<body><div class='grammar_dict'><table class='grammar_dict'>"

    # process the inflections of each word in DpdHeadwords
    for counter, i in enumerate(pd.db):

        # words with ! in the stem are inflected forms 
        # and wil get dealt with under the main headwords 
        if "!" in i.stem:
            pass
        
        # words with '*' in stem are irregular inflections, remove the * for clean processing. 
        if i.stem == "*":
            i.stem = ""
        
        # process indeclinables
        if i.stem == "-":
            data_line = (i.lemma_1, i.pos, "indeclineable")
            html_line = f"<tr><td><b>{i.pos}</b></td><td colspan='5'>indeclineable</td></tr>"

            # grammar_dict update
            if i.lemma_clean not in grammar_dict:
                grammar_dict[i.lemma_clean] = [data_line]
            else:
                if data_line not in grammar_dict[i.lemma_clean]:
                    grammar_dict[i.lemma_clean].append(data_line)

            # grammar_dict_html update
            if i.lemma_clean not in grammar_dict_html:
                grammar_dict_html[i.lemma_clean] = f"{html_header}{html_line}"
                grammar_dict_table[i.lemma_clean] = f"{html_table_header}{html_line}"
            else:
                if html_line not in grammar_dict_html[i.lemma_clean]:
                    grammar_dict_html[i.lemma_clean] += html_line
                    grammar_dict_table[i.lemma_clean] += html_line

        # all other words need an inflection table generated 
        # to find out their grammatical category, i.e. masc nom sg
        else:
            # get template
            template = pd.db_session \
                .query(InflectionTemplates) \
                .filter(InflectionTemplates.pattern == i.pattern) \
                .first()

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
                            row_number > 0
                            and column_number % 2 == 1
                            and column_number > 0
                        ):
                            grammar: str = [row_data[column_number+1]][0][0]

                            for inflection in cell_data:
                                if inflection:
                                    inflected_word = f"{i.stem}{inflection}"
                                    if inflected_word in pd.all_words_set:

                                        data_line = (i.lemma_1, i.pos, grammar)
                                        html_line = "<tr>"
                                        html_line += f"<td><b>{i.pos}</b></td>"
                                        # get grammatical_categories from grammar
                                        grammatical_categories = []
                                        if grammar.startswith("reflx"):
                                            grammatical_categories.append(grammar.split()[0] + " " + grammar.split()[1])
                                            grammatical_categories += grammar.split()[2:]
                                            for grammatical_category in grammatical_categories:
                                                html_line += f"<td>{grammatical_category}</td>"
                                        elif grammar.startswith("in comps"):
                                            html_line += f"<td colspan='3'>{grammar}</td>"
                                        else:
                                            grammatical_categories = grammar.split()
                                            # adding empty values if there are less than 3
                                            while len(grammatical_categories) < 3:
                                                grammatical_categories.append("")
                                            for grammatical_category in grammatical_categories:
                                                html_line += f"<td>{grammatical_category}</td>"
                                        html_line += "<td>of</td>"
                                        html_line += f"<td>{i.lemma_clean}</td>"
                                        html_line += "</tr>"

                                        # grammar_dict update
                                        if inflected_word not in grammar_dict:
                                            grammar_dict[inflected_word] = [data_line]
                                        else:
                                            if data_line not in grammar_dict[inflected_word]:
                                                grammar_dict[inflected_word].append(data_line)

                                        # grammar_dict_html update
                                        if inflected_word not in grammar_dict_html:
                                            grammar_dict_html[inflected_word] = f"{html_header}{html_line}"
                                            grammar_dict_table[inflected_word] = f"{html_table_header}{html_line}"
                                        else:
                                            if html_line not in grammar_dict_html[inflected_word]:
                                                grammar_dict_html[inflected_word] += html_line
                                                grammar_dict_table[inflected_word] += html_line

        if counter % 5000 == 0:
            print(f"{counter:>10,} / {len(pd.db):<10,}{i.lemma_1}")

    # FIXME what about using Jinja tempalte here?

    # clean up the html
    for item in grammar_dict_html:
        grammar_dict_html[item] += "</table></div></body></html>"

    for item in grammar_dict_table:
        grammar_dict_table[item] += "</table></div>"

    # !!! FIXME find out how to remove headings from table with only 1 row

    for item in grammar_dict_table:
        grammar_dict_table[item] += "</tbody></table></div>"
    
    pd.grammar_dict = grammar_dict
    pd.grammar_dict_table = grammar_dict_table
    pd.grammar_dict_html = grammar_dict_html


def save_pickle_and_tsv(pd):
    """Save in pickle and tsv formats for external use."""

    print(f"[green]{'saving pickle and tsv':<40}{len(pd.grammar_dict):>10,}")

    # save pickle file
    print(f"[green]{'saving grammar_dict pickle':<40}{len(pd.grammar_dict):>10,}")
    with open(pd.pth.grammar_dict_pickle_path, "wb") as f:
        pickle.dump(pd.grammar_dict, f)
    
    # save tsv of inflection and table
    print(f"[green]{'saving grammar_dict tsv':<40}{len(pd.grammar_dict_table):>10,}")
    with open(pd.pth.grammar_dict_tsv_path, "w") as f:
        f.write("inflection\thtml\n")
        for inflection, table in pd.grammar_dict_table.items():
            f.write(f"{inflection}\t{table}\n")


def add_to_lookup_table(pd):
    """Add the grammar dict items to the Lookup table."""

    print(f"[green]{'saving to Lookup table':<40}{len(pd.grammar_dict):>10,}")

    lookup_table = pd.db_session.query(Lookup).all()
    results = update_test_add(lookup_table, pd.grammar_dict)
    update_set, test_set, add_set = results

    # update test add
    for i in lookup_table:
        if i.lookup_key in update_set:
            i.grammar_pack(pd.grammar_dict[i.lookup_key])
        elif i.lookup_key in test_set:
            if is_another_value(i, "grammar"):
                i.grammar = ""
            else:
                pd.db_session.delete(i)                
    
    pd.commit_db()

    # add
    add_to_db = []
    for inflection, grammar_data in pd.grammar_dict.items():
        if inflection in add_set:
            add_me = Lookup()
            add_me.lookup_key = inflection
            add_me.grammar_pack(grammar_data)
            add_to_db.append(add_me)

    pd.db_session.add_all(add_to_db)
    pd.commit_db()


def make_data_lists(pd):
    """Make the data_lists to be consumed by GoldenDict and MDict"""
    gd_data_list: List[dict] = []
    for word, html in pd.grammar_dict_html.items():
        synonyms = add_niggahitas([word])

        gd_data_list += [{
            "word": word,
            "definition_html": html,
            "definition_plain": "",
            "synonyms": synonyms
        }]

    # update progdata
    pd.gd_data_list = gd_data_list


def make_goldendict(pd):
    """Export into GoldenDict / Stardict forwat using Simsapa"""
    print(f"[green]{'making goldendict':<40}", end="")

    zip_path = pd.pth.grammar_dict_zip_path

    pd.bookname = "DPD Grammar"
    pd.author = "Bodhirasa"
    pd.description = "<h3>DPD Grammar</h3><p>A table of all the gramamtical possibilities that a particular inflected word may have. For more information please visit the <a href='https://digitalpalidictionary.github.io/grammardict.html' target='_blank'>DPD website</a></p>"
    pd.website = "thtps://digitalpalidictionary.github.io/grammardict.html"

    ifo = ifo_from_opts({
        "bookname": pd.bookname,
        "author": pd.author,
        "description": pd.description,
        "website": pd.website
    })

    export_words_as_stardict_zip(pd.gd_data_list, ifo, zip_path)
    print(f"{'ok':>10}")


def unzip_and_copy_goldendict(pd):
    """Copy the GoldenDict file to a local folder defined in config.ini."""
    print(f"[green]{'unzipping and copying to GD folder':<40}", end="")

    goldendict_path: (Path |str) = goldedict_path()

    if goldendict_path and goldendict_path.exists():
        try:
            with Popen(f'unzip -o {pd.pth.grammar_dict_zip_path} -d "{goldendict_path}"', shell=True, stdout=PIPE, stderr=PIPE) as process:
                stdout, stderr = process.communicate()

                if process.returncode == 0:
                    print(f"{'ok':>10}")
                else:
                    print("[red]Error during unzip and copy:")
                    print(f"Exit Code: {process.returncode}")
                    print(f"Standard Output: {stdout.decode('utf-8')}")
                    print(f"Standard Error: {stderr.decode('utf-8')}")
        except Exception as e:
            print(f"[red]Error during unzip and copy: {e}")
    else:
        print("[red]local GoldenDict directory not found")


def make_mdict(pd):
    """Make an MDict version for OS and Android devices."""
    print(f"[green]{'making mdict':<40}")

    export_to_mdict(
        pd.gd_data_list,
        pd.pth.grammar_dict_mdict_path, 
        pd.bookname,
        pd.description,
        h3_header=True
        )


if __name__ == "__main__":
    main()
