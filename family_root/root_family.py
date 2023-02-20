#!/usr/bin/env python3.10

import re

from rich import print

from db.db_helpers import get_db_session
from db.models import PaliRoot, PaliWord, FamilyRoot
from tools.timeis import tic, toc
from tools.superscripter import superscripter_uni
from root_matrix import generate_root_matrix


def setup():
    global db_session
    db_session = get_db_session("dpd.db")

    root_family_db = db_session.query(PaliWord).filter(
        PaliWord.family_root != "").order_by(
            PaliWord.root_key).group_by(
            PaliWord.root_key, PaliWord.family_root).all()

    global root_family_list
    root_family_list = [(i.root_key, i.family_root) for i in root_family_db]

    global dpd_db
    dpd_db = db_session.query(PaliWord).filter(
        PaliWord.family_root != "").order_by(
        PaliWord.root_key).all()

    global roots_db
    roots_db = db_session.query(PaliRoot).all()

    global bases_dict
    bases_dict = {}


def generate_root_subfamily_html_and_extract_bases():
    print("[green]extracting bases and")
    print("[green]generating html for each root subfamily")

    add_to_db = []

    for x in enumerate(root_family_list):
        counter = x[0]
        root_key = x[1][0]
        subfamily = x[1][1]

        if counter % 500 == 0:
            print(
                f"  {counter:>6,} / {len(root_family_list):<6,}  {subfamily}")

        # !!!!!!!!!!!!! pali alphabetical order !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        subfamily_db = db_session.query(PaliWord).filter(
            PaliWord.family_root == subfamily,
            PaliWord.root_key == root_key
            ).all()

        html_string = "<table class='table_family'>"

        for i in subfamily_db:

            # get bases

            base = re.sub("^.+> ", "", i.root_base)

            if i.root_key not in bases_dict:
                if base != "":
                    bases_dict[i.root_key] = {base}
            else:
                if base != "":
                    bases_dict[i.root_key].add(base)

            # generate html

            if i.meaning_1 == "":
                meaning = i.meaning_2
            else:
                meaning = i.meaning_1
            if i.meaning_lit != "":
                meaning += f"; lit. {i.meaning_lit}"

            html_string += f"<tr><th>{superscripter_uni(i.pali_1)}</th>"
            html_string += f"<td><b>{i.pos}</b></td>"
            html_string += f"<td>{meaning}</td></tr>"

        html_string += "</table>"

        root_family = FamilyRoot(
            root_family=f"{root_key} {subfamily}",
            html=html_string,
            count=len(subfamily_db))

        add_to_db.append(root_family)

        with open(f"xxx delete/root_subfamily/{root_key}.html", "w") as f:
            f.write(html_string)

    db_session.execute(FamilyRoot.__table__.delete())
    db_session.add_all(add_to_db)
    db_session.commit()


def root_grouper(root_group: int):

    root_groups = {
        1: "bhūvādigaṇa",
        2: "rudhādigaṇa",
        3: "divādigaṇa",
        4: "svādigaṇa",
        5: "kiyādigaṇa",
        6: "gahādigaṇa",
        7: "tanādigaṇa",
        8: "curādigaṇa"
    }
    return root_groups.get(root_group, "ERROR!")


def generate_root_info_html():
    print("[green]compiling root info")

    add_to_db = []

    for x in enumerate(roots_db):
        counter = x[0]
        i = x[1]

        if counter % 100 == 0:
            print(
                f"   {counter:>5,} / {len(roots_db):<5,}   {i.root}")

        root_clean = re.sub(" \\d*$", "", i.root)
        root_group_pali = root_grouper(i.root_group)
        try:
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!! pali alphabetical order !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            bases = ", ".join(sorted(bases_dict[i.root], key=len))
        except KeyError:
            bases = "-"

        html_string = ""
        html_string += "<table><tbody>"
        html_string += f"<tr><th>Pāḷi Root:</th><td>{root_clean}"
        html_string += f"<sup>{i.root_has_verb}</sup>"
        html_string += f"{i.root_group} {root_group_pali} + {i.root_sign}"
        html_string += f" ({i.root_meaning})</td></tr>"

        if re.findall(",", bases):
            html_string += f"<tr><th>Bases:</th><td>{bases}</td></tr>"
        else:
            html_string += f"<tr><th>Base:</th><td>{bases}</td></tr>"

        # Root in comps
        if i.root_in_comps != "":
            html_string += "<tr><th>Root in Compounds:</th>"
            html_string += f"<td>{i.root_in_comps}</td></tr>"

        # Dhātupātha
        if i.dhatupatha_root != "-":
            html_string += "<tr><th>Dhātupātha:</th>"
            html_string += f"<td>{i.dhatupatha_root} <i>{i.dhatupatha_pali}"
            html_string += f"</i> ({i.dhatupatha_english}) "
            html_string += f"#{i.dhatupatha_num}</td></tr>"
        else:
            html_string += "<tr><th>Dhātupātha:</th><td>-</td></tr>"

        # Dhātumañjūsa
        if i.dhatumanjusa_root != "-":
            html_string += "<tr><th>Dhātumañjūsa:</th>"
            html_string += f"<td>{i.dhatumanjusa_root} "
            html_string += f"<i>{i.dhatumanjusa_pali}</i> "
            html_string += f"({i.dhatumanjusa_english}) "
            html_string += f"#{i.dhatumanjusa_num}</td></tr>"
        else:
            html_string += "<tr><th>Dhātumañjūsa:</th><td>-</td></tr>"

        # Saddanīti
        if i.dhatumala_root != "-":
            html_string += "<tr><th>Saddanīti:</th>"
            html_string += f"<td>{i.dhatumala_root} <i>{i.dhatumala_pali}</i> "
            html_string += f"({i.dhatumala_english})</td></tr>"
        else:
            html_string += "<tr><th>Saddanīti:</th><td>-</td></tr>"

        # Sanskrit
        html_string += "<tr><th>Sanskrit Root:</th>"
        html_string += f"<td style = 'color:gray'>{i.sanskrit_root} "
        html_string += f"{i.sanskrit_root_class} "
        html_string += f"({i.sanskrit_root_meaning})</td></tr>"

        # Pāṇinīya Dhātupāṭha
        if i.panini_root != "-":
            html_string += "<tr><th>Pāṇinīya Dhātupāṭha:</th>"
            html_string += "<td style = 'color:gray'>"
            html_string += f"{i.panini_root} <i>{i.panini_sanskrit}</i> "
            html_string += f"({i.panini_english})</td></tr>"
        else:
            html_string += "<tr><th>Pāṇinīya Dhātupāṭha:</th><td>-</td></tr>"

        if i.note != "":
            html_string += f"<tr><th>Notes:</th><td>{i.note}</td></tr>"

        html_string += "</tbody></table>"

        count = db_session.query(PaliWord).filter(
            PaliWord.root_key == i.root).count()

        root_info = FamilyRoot(
            root_family=f"{i.root} info",
            html=html_string,
            count=count
        )

        add_to_db.append(root_info)

    db_session.add_all(add_to_db)
    db_session.commit()


def main():
    tic()
    print("[bright_yellow]root families")
    setup()
    generate_root_subfamily_html_and_extract_bases()
    generate_root_info_html()
    generate_root_matrix(db_session)
    db_session.close()
    toc()


if __name__ == "__main__":
    main()
