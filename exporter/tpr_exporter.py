#!/usr/bin/env python3.11

import os
import re
import sqlite3
import pandas as pd
import json

from datetime import date
from zipfile import ZipFile, ZIP_DEFLATED
from sqlalchemy.orm import Session
from rich import print

from html_components import render_dpd_defintion_templ
from helpers import get_paths, ResourcePaths
from db.get_db_session import get_db_session
from db.models import PaliWord, PaliRoot, Sandhi
from tools.pali_sort_key import pali_sort_key
from tools.timeis import tic, toc


TODAY = date.today()
PTH: ResourcePaths = get_paths()
DB_SESSION: Session = get_db_session("dpd.db")


def main():
    tic()
    print("[bright_yellow]generate tpr data")
    tpr_data_list = generate_tpr_data()
    tpr_df, i2h_df = copy_to_sqlite_db(tpr_data_list)
    tpr_updater(tpr_df, i2h_df)
    copy_zip_to_trp_downloads()
    toc()


def generate_tpr_data():
    print("[green]compiling pali word data")

    dpd_db = DB_SESSION.query(PaliWord).all()
    dpd_length = len(dpd_db)
    all_headwords_clean: set = set()
    tpr_data_list = []

    for counter, i in enumerate(dpd_db):
        all_headwords_clean.update(i.pali_clean)

        if counter % 5000 == 0 or counter % dpd_length == 0:
            print(f"{counter:>10,} / {dpd_length:<10,}{i.pali_1:<10}")

        # headword
        html_string = render_dpd_defintion_templ(i)
        html_string = html_string.replace("\n", "").replace("    ", "")
        html_string = re.sub("""<span class\\='g.+span>""", "", html_string)

        # no meaning in context
        if i.meaning_1 == "":
            html_string = re.sub(
                r"<div class='content'><p>",
                fr'<div><p><b>• {i.pali_1}</b>: ',
                html_string)

        # has meaning in context
        else:
            html_string = re.sub(
                r"<div class='content'><p>",
                fr'<div><details><summary><b>{i.pali_1}</b>: ',
                html_string)
            html_string = re.sub(
                r'</p></div>',
                r'</summary>',
                html_string)

            # grammar
            html_string += """<table><tr><th valign="top">Pāḷi</th>"""
            html_string += f"""<td>{i.pali_2}</td></tr>"""
            html_string += """<tr><th valign="top">Grammar</th>"""
            html_string += f"""<td>{i.grammar}"""

            if i.neg != "":
                html_string += f""", {i.neg}"""

            if i.verb != "":
                html_string += f""", {i.verb}"""

            if i.trans != "":
                html_string += f""", {i.trans}"""

            if i.plus_case != "":
                html_string += f""", {i.plus_case}"""

            html_string += """</td></tr>"""
            html_string += """<tr><th valign="top">Meaning</th>"""
            html_string += f"""<td><b>{i.meaning_1}</b>."""

            if i.meaning_lit != "":
                html_string += f"""lit. {i.meaning_lit}"""
            html_string += """</td></tr>"""

            if i.root_key != "":
                html_string += """<tr><th valign="top">Root</th>"""
                html_string += f"""<td>{i.rt.root_clean} {i.rt.root_group} """
                html_string += f"""{i.root_sign} ({i.rt.root_meaning})</td>"""
                html_string += """</tr>"""

                if i.rt.root_in_comps != "":
                    html_string += """<tr><th valign="top">√ in comps</th>"""
                    html_string += f"""<td>{i.rt.root_in_comps}</td></tr>"""

                if i.root_base != "":
                    html_string += """<tr><th valign="top">Base</th>"""
                    html_string += f"""<td>{i.root_base}</td></tr>"""

            if i.construction != "":
                # <br/> is causing an extra line, replace with div
                construction_no_br = re.sub(
                    "(\n)(.+)", "<div>\\2</div>", i.construction)
                html_string += """<tr><th valign="top">Construction</th>"""
                html_string += f"""<td>{construction_no_br}</td></tr>"""

            if i.derivative != "":
                html_string += """<tr><th valign="top">Derivative</th>"""
                html_string += f"""<td>{i.derivative} ({i.suffix})</td></tr>"""

            if i.phonetic != "":
                phonetic = re.sub("\n", ", ", i.phonetic)
                html_string += """<tr><th valign="top">Phonetic</th>"""
                html_string += f"""<td>{phonetic}</td></tr>"""

            if i.compound_type != "" and re.findall(
                    r"\d", i.compound_type) == []:
                comp_constr_no_formatting = re.sub(
                    "<b>|<\\/b>|<i>|<\\/i>", "", i.compound_construction)
                comp_constr_no_formatting = re.sub(
                    "\n", ", ", i.compound_construction)
                html_string += """<tr><th valign="top">Compound</th>"""
                html_string += f"""<td>{ i.compound_type} """
                html_string += f"""({comp_constr_no_formatting})</td></tr>"""

            if i.antonym != "":
                html_string += """<tr><th valign="top">Antonym</th>"""
                html_string += f"""<td>{i.antonym}</td></tr>"""

            if i.synonym != "":
                html_string += """<tr><th valign="top">Synonym</th>"""
                html_string += f"""<td>{i.synonym}</td></tr>"""

            if i.variant != "":
                html_string += """<tr><th valign="top">Variant</th>"""
                html_string += f"""<td>{i.variant}</td></tr>"""

            if i.commentary != "":
                commentary_no_formatting = re.sub(
                    r"<b>|<\/b>|<i>|<\/i>", "", i.commentary)
                commentary_no_formatting = re.sub(
                    "<br>", " ", commentary_no_formatting)
                commentary_no_formatting = re.sub(
                    "\n", " ", commentary_no_formatting)
                html_string += """<tr><th valign="top">Commentary</th>"""
                html_string += f"""<td>{commentary_no_formatting}</td></tr>"""

            if i.notes != "":
                notes_no_formatting = re.sub(
                    "<b>|<\\/b>|<i>|<\\/i>", "", i.notes)
                notes_no_formatting = re.sub(
                    "<br\\/>", ". ", notes_no_formatting)
                notes_no_formatting = re.sub(
                    "\n", ". ", notes_no_formatting)
                html_string += """<tr><th valign="top">Notes</th>"""
                html_string += f"""<td>{notes_no_formatting}</td></tr>"""

            if i.cognate != "":
                html_string += """<tr><th valign="top">Cognate</th>"""
                html_string += f"""<td>{i.cognate}</td></tr>"""

            if i.link != "":
                link_no_br = re.sub("<br\\/>", " ", i.link)
                link_no_br = re.sub("\n.+", "", link_no_br)
                html_string += """<tr><th valign="top">Link</th>"""
                html_string += f"""<td><a href="{link_no_br}">"""
                html_string += f"""{link_no_br}</a></td></tr>"""

            if i.non_ia != "":
                html_string += """<tr><th valign="top">Non IA</th>"""
                html_string += f"""<td>{i.non_ia}</td></tr>"""

            if i.sanskrit != "":
                sanskrit = i.sanskrit.replace("\n", "")
                html_string += """<tr><th valign="top">Sanskrit</th>"""
                html_string += f"""<td>{sanskrit}</td></tr>"""

            if i.root_key != "":
                if i.rt.sanskrit_root != "":
                    sk_root_meaning = re.sub(
                        "'", "", i.rt.sanskrit_root_meaning)
                    html_string += """<tr><th valign="top">Sanskrit Root</th>"""
                    html_string += f"""<td>{i.rt.sanskrit_root} {i.rt.sanskrit_root_class} ({sk_root_meaning})</td></tr>"""

            html_string += f"""<tr><td colspan="2"><a href="https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={i.pali_link}&entry.1433863141=TPR%20{TODAY}" target="_blank">Submit a correction</a></td></tr>"""
            html_string += """</table>"""
            html_string += """</details></div>"""

        html_string = re.sub("'", "’", html_string)

        tpr_data_list += [{
            "word": i.pali_1,
            "definition": f"<p>{html_string}</p>",
            "book_id": 11}]

    # add roots
    print("[green]compiling roots data")

    roots_db = DB_SESSION.query(PaliRoot).all()
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
                "word": r.root_clean,
                "definition": f"{html_string}",
                "book_id": 11}]

            html_string = ""
            new_root = True

    # sandhi splitter
    print("[green]compiling sandhi data")

    sandhi_db = DB_SESSION.query(Sandhi).all()

    for counter, i in enumerate(sandhi_db):

        if i.sandhi not in all_headwords_clean:
            html_string = "<div><p>"
            splits = json.loads(i.split)
            for split in splits:
                if "<i>" in split:
                    html_string += split.replace("<i>", "").replace("</i>", "")
                else:
                    html_string += split
                if split != splits[-1]:
                    html_string += " <br>"
                else:
                    html_string += "</div></p>"
                    tpr_data_list += [{
                        "word": i.sandhi,
                        "definition": html_string,
                        "book_id": 11}]

        if counter % 5000 == 0:
            print(f"{counter:>10,} / {len(sandhi_db):<10,}{i.sandhi:<10}")

    return tpr_data_list


def copy_to_sqlite_db(tpr_data_list):
    print("[green]copying data_list to tpr db", end=" ")

    # data frames
    tpr_df = pd.DataFrame(tpr_data_list)
    i2h_df = pd.read_csv("share/inflection_to_headwords_dict.tsv", sep="\t")

    try:
        conn = sqlite3.connect(
            '../../../../.local/share/tipitaka_pali_reader/tipitaka_pali.db')
        c = conn.cursor()

        # dpd table
        c.execute("DROP TABLE if exists dpd")
        c.execute("CREATE TABLE dpd (word, definition, book_id)")
        tpr_df.to_sql('dpd', conn, if_exists='append', index=False)

        # inflection_to_headwords
        c.execute("DROP TABLE if exists dpd_inflections_to_headwords")
        c.execute(
            "CREATE TABLE dpd_inflections_to_headwords (inflection, headwords)")

        i2h_df.to_sql(
            'dpd_inflections_to_headwords',
            conn, if_exists='append', index=False)
        print("[white]ok")

    except Exception as e:
        print("[red] an error occurred copying to db")
        print(f"[red]{e}")

    conn.close()

    return tpr_df, i2h_df


def tpr_updater(tpr_df, i2h_df):
    print("[green]making tpr sql updater")

    sql_string = ""
    sql_string += "BEGIN TRANSACTION;\n"
    sql_string += "DELETE FROM dpd_inflections_to_headwords;\n"
    sql_string += "DELETE FROM dpd;\n"
    sql_string += "COMMIT;\n"
    sql_string += "BEGIN TRANSACTION;\n"

    print("writing inflections to headwords")

    for row in range(len(i2h_df)):
        inflection = i2h_df.iloc[row, 0]
        headword = i2h_df.iloc[row, 1]
        headword = headword.replace("'", "''")
        if row % 50000 == 0:
            print(f"{row:>10,} / {len(i2h_df):<10,}{inflection:<10}")
        sql_string += f"""INSERT INTO "dpd_inflections_to_headwords" \
("inflection", "headwords") VALUES ('{inflection}', '{headword}');\n"""

    print("writing dpd")

    for row in range(len(tpr_df)):
        word = tpr_df.iloc[row, 0]
        definition = tpr_df.iloc[row, 1]
        definition = definition.replace("'", "''")
        book_id = tpr_df.iloc[row, 2]
        if row % 5000 == 0:
            print(f"{row:>10,} / {len(tpr_df):<10,}{word:<10}")
        sql_string += f"""INSERT INTO "dpd" ("word","definition","book_id")\
 VALUES ('{word}', '{definition}', {book_id});\n"""

    sql_string += "COMMIT;\n"

    with open(PTH.tpr_sql_file_path, "w") as f:
        f.write(sql_string)


def copy_zip_to_trp_downloads():
    print("upating tpr_downlaods")

    with open(PTH.tpr_download_list_path) as f:
        download_list = json.load(f)

    day = TODAY.day
    month = TODAY.month
    month_str = TODAY.strftime("%B")
    year = TODAY.year

    uposathas = [
        date(2023, 1, 6),
        date(2023, 2, 5),
        date(2023, 3, 6),
        date(2023, 4, 5),
        date(2023, 5, 4),
        date(2023, 6, 3),
        date(2023, 7, 2),
        date(2023, 8, 1),
        date(2023, 8, 31),
        date(2023, 9, 29),
        date(2023, 10, 29),
        date(2023, 11, 27),
        date(2023, 12, 27),
        ]

    if TODAY in uposathas:
        version = "release"
    else:
        version = "beta"

    file_path = PTH.tpr_sql_file_path
    file_name = "dpd.sql"

    def _zip_it_up(file_path, file_name, output_file):
        with ZipFile(output_file, 'w', ZIP_DEFLATED) as zipfile:
            zipfile.write(file_path, file_name)

    def _file_size(output_file):
        filestat = os.stat(output_file)
        filesize = f"{filestat.st_size/1000/1000:.1f}"
        return filesize

    if version == "release":
        print("[green]upating release version")

        output_file = PTH.tpr_release_path
        _zip_it_up(file_path, file_name, output_file)
        filesize = _file_size(output_file)

        dpd_info = {
            "name": f"DPD {month_str} {year} release",
            "release_date": f"{day}.{month}.{year}",
            "type": "dictionary",
            "url": "https://github.com/bksubhuti/tpr_downloads/raw/master/download_source_files/dictionaries/dpd.zip",
            "filename": "dpd.sql",
            "size": f"{filesize} MB"
        }

        download_list[2] = dpd_info

    if version == "beta":
        print("[green]upating beta version")

        output_file = PTH.tpr_beta_path
        _zip_it_up(file_path, file_name, output_file)
        filesize = _file_size(output_file)

        dpd_beta_info = {
            "name": "DPD Beta",
            "release_date": f"{day}.{month}.{year}",
            "type": "dictionary",
            "url": "https://github.com/bksubhuti/tpr_downloads/raw/master/download_source_files/dictionaries/dpd_beta.zip",
            "filename": "dpd.sql",
            "size": f"{filesize} MB"
        }

        download_list[11] = dpd_beta_info

    with open(PTH.tpr_download_list_path, "w") as f:
        f.write(json.dumps(download_list, indent=4))


if __name__ == "__main__":
    main()
