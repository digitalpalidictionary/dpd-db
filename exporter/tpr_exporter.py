#!/usr/bin/env python3

"""Export simplified DPD data for integration with Tipitaka Pali Reader (TPR)."""

import csv
import json
import os
import pandas as pd
import re
import sqlite3

from rich import print
from mako.template import Template
from sqlalchemy.orm import Session
from zipfile import ZipFile, ZIP_DEFLATED

from db.get_db_session import get_db_session
from db.models import PaliWord, PaliRoot, Sandhi
from export_dpd import render_dpd_definition_templ
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.headwords_clean_set import make_clean_headwords_set
from tools.uposatha_day import uposatha_today
from helpers import TODAY



def main():
    tic()
    print("[bright_yellow]generate tpr data")

    pth = ProjectPaths()
    print(pth.tpr_release_path)

    if pth.tpr_release_path.exists():

        db_session: Session = get_db_session(pth.dpd_db_path)
        dpd_db = db_session.query(PaliWord).all()
        all_headwords_clean = make_clean_headwords_set(dpd_db)
        tpr_data_list = generate_tpr_data(pth, db_session, dpd_db, all_headwords_clean)
        sandhi_data_list = generate_sandhi_data(db_session, all_headwords_clean)
        write_tsvs(pth, tpr_data_list, sandhi_data_list)
        tpr_df, i2h_df, sandhi_df = copy_to_sqlite_db(pth, tpr_data_list, sandhi_data_list)
        tpr_updater(pth, tpr_df, i2h_df, sandhi_df)
        copy_zip_to_tpr_downloads(pth)
        toc()
    
    else:
        print("[red]tpr_downloads directory does not exist")
        print("it's not essential to create the dictionary")


def generate_tpr_data(pth: ProjectPaths, db_session: Session, dpd_db, __all_headwords_clean__):
    print("[green]compiling pali word data")
    dpd_length = len(dpd_db)
    tpr_data_list = []
    dpd_definition_templ = Template(filename=str(pth.dpd_definition_templ_path))

    for counter, i in enumerate(dpd_db):

        if counter % 5000 == 0 or counter % dpd_length == 0:
            print(f"{counter:>10,} / {dpd_length:<10,}{i.pali_1:<10}")

        # headword
        html_string = render_dpd_definition_templ(pth, i, dpd_definition_templ)
        html_string = html_string.replace("\n", "").replace("    ", "")
        html_string = re.sub("""<span class\\='g.+span>""", "", html_string)

        # no meaning in context
        if not i.meaning_1:
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
                    html_string += """<tr><th valign="top">√ in comps</th>"""
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

    roots_db = db_session.query(PaliRoot).all()
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

    return tpr_data_list


def generate_sandhi_data(db_session: Session, all_headwords_clean):
    # deconstructor
    print("[green]compiling sandhi data")

    sandhi_db = db_session.query(Sandhi).all()
    sandhi_data_list = []

    for counter, i in enumerate(sandhi_db):

        if i.sandhi not in all_headwords_clean:
            if "variant" not in i.split and "spelling" not in i.split:
                sandhi_data_list += [{
                    "word": i.sandhi,
                    "breakup": i.split}]

        if counter % 50000 == 0:
            print(f"{counter:>10,} / {len(sandhi_db):<10,}{i.sandhi:<10}")

    return sandhi_data_list


def write_tsvs(pth: ProjectPaths, tpr_data_list, sandhi_data_list):
    """Write TSV files of dpd, i2h and deconstructor."""
    print("[green]writing tsv files")

    # write dpd_tsv
    with open(pth.tpr_dpd_tsv_path, "w") as f:
        f.write("word\tdefinition\tbook_id\n")
        for i in tpr_data_list:
            f.write(f"{i['word']}\t{i['definition']}\t{i['book_id']}\n")

    # write deconstructor tsv
    field_names = ["word", "breakup"]
    with open(pth.tpr_deconstructor_tsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=field_names, delimiter="\t")
        writer.writeheader()
        writer.writerows(sandhi_data_list)


def copy_to_sqlite_db(pth: ProjectPaths, tpr_data_list, sandhi_data_list):
    print("[green]copying data_list to tpr db", end=" ")

    # data frames
    tpr_df = pd.DataFrame(tpr_data_list)
    i2h_df = pd.read_csv(pth.tpr_i2h_tsv_path, sep="\t")
    sandhi_df = pd.DataFrame(sandhi_data_list)

    try:
        conn = sqlite3.connect(
            '../../.local/share/tipitaka_pali_reader/tipitaka_pali.db')
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

        # dpd_word_split
        c.execute("DROP TABLE if exists dpd_word_split")
        c.execute(
            "CREATE TABLE dpd_word_split (word, breakup)")
        sandhi_df.to_sql(
            'dpd_word_split',
            conn, if_exists='append', index=False)
        print("[white]ok")

        conn.close()

        return tpr_df, i2h_df, sandhi_df

    except Exception as e:
        print("[red] an error occurred copying to db")
        print(f"[red]{e}")
        return tpr_df, i2h_df, sandhi_df


def tpr_updater(pth: ProjectPaths, tpr_df, i2h_df, sandhi_df):
    print("[green]making tpr sql updater")

    sql_string = ""
    sql_string += "BEGIN TRANSACTION;\n"
    sql_string += "DELETE FROM dpd;\n"
    sql_string += "DELETE FROM dpd_inflections_to_headwords;\n"
    sql_string += "DELETE FROM dpd_word_split;\n"
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
        if row % 50000 == 0:
            print(f"{row:>10,} / {len(tpr_df):<10,}{word:<10}")
        sql_string += f"""INSERT INTO "dpd" ("word","definition","book_id")\
 VALUES ('{word}', '{definition}', {book_id});\n"""

    print("writing deconstructor")

    for row in range(len(sandhi_df)):
        word = sandhi_df.iloc[row, 0]
        breakup = sandhi_df.iloc[row, 1]
        if row % 50000 == 0:
            print(f"{row:>10,} / {len(sandhi_df):<10,}{word:<10}")
        sql_string += f"""INSERT INTO "dpd_word_split" ("word","breakup")\
 VALUES ('{word}', '{breakup}');\n"""

    sql_string += "COMMIT;\n"

    with open(pth.tpr_sql_file_path, "w") as f:
        f.write(sql_string)


def copy_zip_to_tpr_downloads(pth: ProjectPaths):
    print("upating tpr_downlaods")

    if not pth.tpr_download_list_path.exists():
        print("[red]tpr_downloads repo does not exist, download")
        print("[red]https://github.com/bksubhuti/tpr_downloads")
        print("[red]to /resources/ folder")
    else:
        with open(pth.tpr_download_list_path) as f:
            download_list = json.load(f)

        day = TODAY.day
        month = TODAY.month
        month_str = TODAY.strftime("%B")
        year = TODAY.year

        if uposatha_today():
            version = "release"
        else:
            version = "beta"

        file_path = pth.tpr_sql_file_path
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

            output_file = pth.tpr_release_path
            _zip_it_up(file_path, file_name, output_file)
            filesize = _file_size(output_file)

            dpd_info = {
                "name": f"DPD {month_str} {year} release",
                "release_date": f"{day}.{month}.{year}",
                "type": "dictionary",
                "url": "https://github.com/bksubhuti/tpr_downloads/raw/master/release_zips/dpd.zip",
                "filename": "dpd.sql",
                "size": f"{filesize} MB"
            }

            download_list[5] = dpd_info

        if version == "beta":
            print("[green]upating beta version")

            output_file = pth.tpr_beta_path
            _zip_it_up(file_path, file_name, output_file)
            filesize = _file_size(output_file)

            dpd_beta_info = {
                "name": "DPD Beta",
                "release_date": f"{day}.{month}.{year}",
                "type": "dictionary",
                "url": "https://github.com/bksubhuti/tpr_downloads/raw/master/release_zips/dpd_beta.zip",
                "filename": "dpd.sql",
                "size": f"{filesize} MB"
            }

            download_list[14] = dpd_beta_info

        with open(pth.tpr_download_list_path, "w") as f:
            f.write(json.dumps(download_list, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
