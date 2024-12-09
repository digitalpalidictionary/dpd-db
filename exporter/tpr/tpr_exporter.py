#!/usr/bin/env python3

"""Export simplified DPD data for integration with Tipitaka Pali Reader (TPR)."""

import csv
import json
import os
import pandas as pd
import re
import sqlite3

from mako.template import Template
from sqlalchemy.orm import Session
from zipfile import ZipFile, ZIP_DEFLATED

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot, Lookup
from exporter.goldendict.export_dpd import render_dpd_definition_templ
from tools.configger import config_test, config_read
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import p_green, p_green_title, p_red, p_title, p_yes
from tools.tic_toc import tic, toc
from tools.headwords_clean_set import make_clean_headwords_set
from tools.tsv_read_write import read_tsv
from tools.uposatha_day import uposatha_today
from exporter.goldendict.helpers import TODAY


class ProgData():
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)
        self.dpd_db = self.make_dpd_db()
        
        self.all_headwords_clean: set[str]

        self.tpr_data_list: list[dict[str, str]]
        self.deconstructor_data_list: list[dict[str, str]]
        self.i2h_data_list: list[dict[str, str]]
        
        self.tpr_df: pd.DataFrame
        self.i2h_df: pd.DataFrame
        self.deconstructor_df: pd.DataFrame
    
    def make_dpd_db(self):
        dpd_db = self.db_session.query(DpdHeadword).all()
        dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))
        return dpd_db

def main():

    tic()
    
    p_title("generate tpr data")

    if not config_test("exporter", "make_tpr", "yes"):
        p_green_title("disabled in config.ini")
        toc()
        return
        
    g = ProgData()

    if g.pth.tpr_release_path.exists():
        g.all_headwords_clean = make_clean_headwords_set(g.dpd_db)
        generate_tpr_data(g)
        generate_deconstructor_data(g)
        add_spelling_mistakes(g)
        add_variants(g)
        add_roots_to_i2h(g)
        write_tsvs(g)
        copy_to_sqlite_db(g)
        tpr_updater(g)
        copy_zip_to_tpr_downloads(g)
        toc()
    
    else:
        p_red("[red]tpr_downloads directory does not exist")
        p_red("it's not essential to create the dictionary")


def generate_tpr_data(g: ProgData):
    p_green("compiling dpd headword data")
    dpd_length = len(g.dpd_db)
    tpr_data_list = []
    dpd_definition_templ = Template(filename=str(g.pth.dpd_definition_templ_path))

    for counter, i in enumerate(g.dpd_db):

        # headword
        html_string = render_dpd_definition_templ(
            g.pth, i, dpd_definition_templ, None, None)
        html_string = html_string.replace("\n", "").replace("    ", "")
        html_string = re.sub("""<span class\\='g.+span>""", "", html_string)

        # no meaning in context
        if not i.meaning_1:
            html_string = re.sub(
                r"<div class='content'><p>",
                fr'<div><p><b>• {i.lemma_1}</b>: ',
                html_string)

        # has meaning in context
        else:
            html_string = re.sub(
                r"<div class='content'><p>",
                fr'<div><details><summary><b>{i.lemma_1}</b>: ',
                html_string)
            html_string = re.sub(
                r'</p></div>',
                r'</summary>',
                html_string)

            # grammar
            html_string += """<table><tr><th valign="top">Pāḷi</th>"""
            html_string += f"""<td>{i.lemma_2}</td></tr>"""
            html_string += """<tr><th valign="top">IPA</th>"""
            html_string += f"""<td>/{i.lemma_ipa}/</td></tr>"""
            html_string += """<tr><th valign="top">Grammar</th>"""
            html_string += f"""<td>{i.grammar}"""

            if i.neg:
                html_string += f""", {i.neg}"""

            if i.verb:
                html_string += f""", {i.verb}"""

            if i.trans:
                html_string += f""", {i.trans}"""

            if i.plus_case:
                html_string += f""" ({i.plus_case})"""

            html_string += """</td></tr>"""

            if i.root_key:
                html_string += """<tr><th valign="top">Root</th>"""
                html_string += f"""<td>{i.rt.root_clean} {i.rt.root_group} """
                html_string += f"""{i.root_sign} ({i.rt.root_meaning})</td>"""
                html_string += """</tr>"""

                if i.rt.root_in_comps:
                    html_string += """<tr><th valign="top">√ In Sandhi</th>"""
                    html_string += f"""<td>{i.rt.root_in_comps}</td></tr>"""

                if i.root_base:
                    html_string += """<tr><th valign="top">Base</th>"""
                    html_string += f"""<td>{i.root_base}</td></tr>"""

            if i.construction:
                # <br/> is causing an extra line, replace with div
                construction_br = i.construction.replace("\n", "<br>")
                html_string += """<tr><th valign="top">Construction</th>"""
                html_string += f"""<td>{construction_br}</td></tr>"""

            if i.derivative:
                html_string += """<tr><th valign="top">Derivative</th>"""
                html_string += f"""<td>{i.derivative} ({i.suffix})</td></tr>"""

            if i.phonetic:
                phonetic = re.sub("\n", "<br>", i.phonetic)
                html_string += """<tr><th valign="top">Phonetic</th>"""
                html_string += f"""<td>{phonetic}</td></tr>"""

            if i.compound_type and re.findall(
                    r"\d", i.compound_type) == []:
                comp_constr_br = re.sub(
                    "\n", "<br>", i.compound_construction)
                html_string += """<tr><th valign="top">Compound</th>"""
                html_string += f"""<td>{ i.compound_type} """
                html_string += f"""({comp_constr_br})</td></tr>"""

            if i.antonym:
                html_string += """<tr><th valign="top">Antonym</th>"""
                html_string += f"""<td>{i.antonym}</td></tr>"""

            if i.synonym:
                html_string += """<tr><th valign="top">Synonym</th>"""
                html_string += f"""<td>{i.synonym}</td></tr>"""

            if i.variant:
                html_string += """<tr><th valign="top">Variant</th>"""
                html_string += f"""<td>{i.variant}</td></tr>"""

            if  (i.commentary and i.commentary != "-"):
                commentary_no_formatting = re.sub(
                    "\n", "<br>", i.commentary)
                html_string += """<tr><th valign="top">Commentary</th>"""
                html_string += f"""<td>{commentary_no_formatting}</td></tr>"""

            if i.notes:
                notes_no_formatting = i.notes.replace("\n", "<br>")
                html_string += """<tr><th valign="top">Notes</th>"""
                html_string += f"""<td>{notes_no_formatting}</td></tr>"""

            if i.cognate:
                html_string += """<tr><th valign="top">Cognate</th>"""
                html_string += f"""<td>{i.cognate}</td></tr>"""

            if i.link:
                link_br = i.link.replace("\n", "<br>")
                html_string += """<tr><th valign="top">Link</th>"""
                html_string += f"""<td><a href="{link_br}">"""
                html_string += f"""{link_br}</a></td></tr>"""

            if i.non_ia:
                html_string += """<tr><th valign="top">Non IA</th>"""
                html_string += f"""<td>{i.non_ia}</td></tr>"""

            if i.sanskrit:
                sanskrit = i.sanskrit.replace("\n", "")
                html_string += """<tr><th valign="top">Sanskrit</th>"""
                html_string += f"""<td>{sanskrit}</td></tr>"""

            if i.root_key:
                if i.rt.sanskrit_root:
                    sk_root_meaning = re.sub(
                        "'", "", i.rt.sanskrit_root_meaning)
                    html_string += """<tr><th valign="top">Sanskrit Root</th>"""
                    html_string += f"""<td>{i.rt.sanskrit_root} {i.rt.sanskrit_root_class} ({sk_root_meaning})</td></tr>"""

            html_string += f"""<tr><td colspan="2"><a href="https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={i.lemma_link}&entry.1433863141=TPR%20{TODAY}" target="_blank">Submit a correction</a></td></tr>"""
            html_string += """</table>"""
            html_string += """</details></div>"""

        html_string = re.sub("'", "’", html_string)

        tpr_data_list += [{
            "id": i.id,
            "word": i.lemma_1,
            "definition": f"<p>{html_string}</p>",
            "book_id": 11}]
    p_yes(dpd_length)

    # add roots
    p_green("compiling roots data")

    roots_db = g.db_session.query(DpdRoot).all()
    roots_db = sorted(roots_db, key=lambda x: pali_sort_key(x.root))
    html_string = ""
    new_root = True

    for counter, r in enumerate(roots_db):

        if new_root:
            html_string += "<div><p>"

        html_string += f"""<b>{r.root_clean}</b> """
        html_string += f"""{r.root_group} {r.root_sign} ({r.root_meaning})"""

        try:
            next_root_clean = roots_db[counter + 1].root_clean
        except Exception:
            next_root_clean = ""

        if r.root_clean == next_root_clean:
            html_string += " <br>"
            new_root = False
        else:
            html_string += """</p></div>"""

            tpr_data_list += [{
                "id": 0,
                "word": r.root_clean,
                "definition": f"{html_string}",
                "book_id": 11}]

            html_string = ""
            new_root = True

    g.tpr_data_list = tpr_data_list
    p_yes(counter)


def generate_deconstructor_data(g: ProgData):
    """Compile deconstructor data."""
    p_green("compiling deconstructor data")

    deconstructor_db = g.db_session.query(Lookup) \
        .filter(Lookup.deconstructor != "") \
        .all()
    deconstructor_db = sorted(
        deconstructor_db, key=lambda x: pali_sort_key(x.lookup_key))
    deconstructor_data_list = []

    for counter, i in enumerate(deconstructor_db):

        if i.lookup_key not in g.all_headwords_clean:
            deconstruction = ",".join(i.deconstructor_unpack).strip() # remove stray \r

            deconstructor_data_list += [{
                "word": i.lookup_key,
                "breakup": deconstruction}]
    
    g.deconstructor_data_list = deconstructor_data_list
    p_yes(counter)


def add_variants(g):
    """Add variant readings to deconstructor data"""
    p_green("compiling variants")
    
    variants_db = g.db_session \
        .query(Lookup) \
        .filter(Lookup.variant != "") \
        .all()
    variants_db = sorted(
        variants_db, key=lambda x: pali_sort_key(x.lookup_key))

    for i in variants_db:
        variant = f"variant reading of <i>{i.variants_unpack[0]}</i>"
        g.deconstructor_data_list += [{
            "word": i.lookup_key,
            "breakup": variant}]
    
    p_yes(len(variants_db))


def add_spelling_mistakes(g):
    """Add spelling mistakes to deconstructor data"""
    p_green("compiling spelling mistakes")
    

    spelling_db = g.db_session \
        .query(Lookup) \
        .filter(Lookup.spelling != "") \
        .all()
    spelling_db = sorted(
        spelling_db, key=lambda x: pali_sort_key(x.lookup_key))

    for i in spelling_db:
        spelling = f"incorrect spelling of <i>{i.spelling_unpack[0]}</i>"
        g.deconstructor_data_list += [{
            "word": i.lookup_key,
            "breakup": spelling}]
    
    p_yes(len(spelling_db))


def add_roots_to_i2h(g):
    """Add roots to inflections to headwords"""
    p_green("adding roots to lookup")

    i2h_data = read_tsv(g.pth.tpr_i2h_tsv_path)
    i2h_dict = {}
    for i in i2h_data[1:]:
        inflection, headwords = i
        i2h_dict[inflection] = headwords.split(",")

    roots_db = g.db_session.query(DpdRoot).all()

    for r in roots_db:

        # add clean roots
        if r.root_clean not in i2h_dict:
            i2h_dict[r.root_clean] = [r.root_clean]

        # add roots no sign
        if r.root_no_sign not in i2h_dict:
            i2h_dict[r.root_no_sign] = [r.root_clean]

    i2h_data_list = []
    for inflection, headwords in i2h_dict.items():
            headwords = ",".join(headwords)
            i2h_data_list.append(
                {
                    "inflection": inflection,
                    "headwords": headwords
                })
    
    g.i2h_data_list = i2h_data_list
    p_yes(len(roots_db))



def write_tsvs(g: ProgData):
    """Write TSV files of dpd, deconstructor."""
    p_green("writing tsv files")

    # write dpd_tsv
    with open(g.pth.tpr_dpd_tsv_path, "w") as f:
        f.write("id\tword\tdefinition\tbook_id\n")
        for i in g.tpr_data_list:
            f.write(f"{i['id']}\t{i['word']}\t{i['definition']}\t{i['book_id']}\n")

    # write deconstructor tsv
    field_names = ["word", "breakup"]
    with open(g.pth.tpr_deconstructor_tsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=field_names, delimiter="\t")
        writer.writeheader()
        writer.writerows(g.deconstructor_data_list)
    p_yes("OK")


def copy_to_sqlite_db(g: ProgData):
    p_green("copying data_list to tpr db")

    # data frames
    tpr_df = pd.DataFrame(g.tpr_data_list)
    i2h_df = pd.DataFrame(g.i2h_data_list)
    deconstructor_df = pd.DataFrame(g.deconstructor_data_list)
    tpr_db_path = config_read("tpr", "db_path")

    if tpr_db_path:
        try:
            conn = sqlite3.connect(tpr_db_path)
            c = conn.cursor()

            # dpd table
            c.execute("DROP TABLE if exists dpd")
            c.execute(
                """CREATE TABLE "dpd" (
                    "id" INTEGER,
                    "word" TEXT,
                    "definition" TEXT, 
                    "book_id" INTEGER,
                    "has_inflections" INTEGER DEFAULT 0,
                    "has_root_family" INTEGER DEFAULT 0,
                    "has_compound_family" INTEGER DEFAULT 0,
                    "has_word_family" INTEGER DEFAULT 0,
                    "has_freq" INTEGER DEFAULT 0);
                """)
            

            tpr_df.to_sql('dpd', conn, if_exists='append', index=False)

            # inflection_to_headwords
            c.execute("DROP TABLE if exists dpd_inflections_to_headwords")
            c.execute(
                "CREATE TABLE dpd_inflections_to_headwords (inflection, headwords)")
            i2h_df.to_sql(
                'dpd_inflections_to_headwords',
                conn, if_exists='append', index=False)

            # dpd_word_split
            c.execute("DROP TABLE if exists dpd_word_split")
            c.execute(
                "CREATE TABLE dpd_word_split (word, breakup)")
            deconstructor_df.to_sql(
                'dpd_word_split',
                conn, if_exists='append', index=False)
            p_yes("OK")

            conn.close()

        except Exception as e:
            p_red("an error occurred copying to db")
            p_red(e)

    g.tpr_df = tpr_df
    g.i2h_df = i2h_df
    g.deconstructor_df = deconstructor_df


def tpr_updater(g: ProgData):
    p_green("making tpr sql updater")

    sql_string = ""
    sql_string += "BEGIN TRANSACTION;\n"
    # sql_string += "DROP TABLE IF EXISTS dpd;\n"
    # sql_string += """CREATE TABLE dpd ("id" INTEGER, "word" TEXT, "definition" TEXT, "book_id" INTEGER, "has_inflections" INTEGER DEFAULT 0, "has_root_family" INTEGER DEFAULT 0, has_compound_family" INTEGER DEFAULT 0, "has_word_family" INTEGER DEFAULT 0, "has_freq" INTEGER DEFAULT 0);\n"""
    sql_string += "DELETE FROM dpd;\n"
    sql_string += "DELETE FROM dpd_inflections_to_headwords;\n"
    sql_string += "DELETE FROM dpd_word_split;\n"
    sql_string += "COMMIT;\n"
    sql_string += "BEGIN TRANSACTION;\n"

    for row in range(len(g.i2h_df)):
        inflection = g.i2h_df.iloc[row, 0]
        headword = g.i2h_df.iloc[row, 1]
        headword = headword.replace("'", "''")  #type:ignore
        sql_string += f"""INSERT INTO "dpd_inflections_to_headwords" \
("inflection", "headwords") VALUES ('{inflection}', '{headword}');\n"""

    for row in range(len(g.tpr_df)):
        id = g.tpr_df.iloc[row, 0]
        word = g.tpr_df.iloc[row, 1]
        definition = g.tpr_df.iloc[row, 2]
        definition = definition.replace("'", "''") #type:ignore
        book_id = g.tpr_df.iloc[row, 3]
        sql_string += f"""INSERT INTO "dpd" ("id", "word", "definition", "book_id")\
 VALUES ({id}, '{word}', '{definition}', {book_id});\n"""

    for row in range(len(g.deconstructor_df)):
        word = g.deconstructor_df.iloc[row, 0]
        breakup = g.deconstructor_df.iloc[row, 1]
        sql_string += f"""INSERT INTO "dpd_word_split" ("word", "breakup")\
 VALUES ('{word}', '{breakup}');\n"""
    
    sql_string += "COMMIT;\n"

    with open(g.pth.tpr_sql_file_path, "w") as f:
        f.write(sql_string)
    p_yes("OK")


def copy_zip_to_tpr_downloads(g: ProgData):
    p_green("updating tpr_downloads")

    if not g.pth.tpr_download_list_path.exists():
        p_red("tpr_downloads repo does not exist, download")
        p_red("https://github.com/bksubhuti/tpr_downloads")
        p_red("to /resources/ folder")
    else:
        with open(g.pth.tpr_download_list_path) as f:
            download_list = json.load(f)

        day = TODAY.day
        month = TODAY.month
        month_str = TODAY.strftime("%B")
        year = TODAY.year

        if uposatha_today():
            version = "release"
        else:
            version = "beta"

        file_path = g.pth.tpr_sql_file_path
        file_name = "dpd.sql"

        def _zip_it_up(file_path, file_name, output_file):
            with ZipFile(output_file, 'w', ZIP_DEFLATED) as zipfile:
                zipfile.write(file_path, file_name)

        def _file_size(output_file):
            filestat = os.stat(output_file)
            filesize = f"{filestat.st_size/1000/1000:.1f}"
            return filesize

        if version == "release":

            output_file = g.pth.tpr_release_path
            _zip_it_up(file_path, file_name, output_file)
            filesize = _file_size(output_file)

            dpd_info = {
                "name": f"DPD {month_str} {year} release",
                "release_date": f"{day}.{month}.{year}",
                "type": "dictionary",
                "category": "Dictionaries",
                "url": "https://github.com/bksubhuti/tpr_downloads/raw/master/release_zips/dpd.zip",
                "filename": "dpd.sql",
                "size": f"{filesize} MB"
            }

            download_list[7] = dpd_info

        if version == "beta":

            output_file = g.pth.tpr_beta_path
            _zip_it_up(file_path, file_name, output_file)
            filesize = _file_size(output_file)

            dpd_beta_info = {
                "name": "DPD Beta",
                "release_date": f"{day}.{month}.{year}",
                "type": "dictionary",
                "category": "Other Beta",
                "url": "https://github.com/bksubhuti/tpr_downloads/raw/master/release_zips/dpd_beta.zip",
                "filename": "dpd.sql",
                "size": f"{filesize} MB"
            }

            download_list[27] = dpd_beta_info

        with open(g.pth.tpr_download_list_path, "w") as f:
            f.write(json.dumps(download_list, indent=4, ensure_ascii=False))
    
    p_yes(version)


if __name__ == "__main__":
    main()

