#!/usr/bin/env python3.11

import re

from rich import print

from root_matrix import generate_root_matrix
from db.get_db_session import get_db_session
from db.models import PaliRoot, PaliWord, FamilyRoot
from tools.timeis import tic, toc
from tools.superscripter import superscripter_uni
from tools.make_meaning import make_meaning
from tools.pali_sort_key import pali_sort_key


def setup():
    global db_session
    db_session = get_db_session("dpd.db")

    root_family_db = db_session.query(PaliWord).filter(
        PaliWord.family_root != "").order_by(
            PaliWord.root_key).group_by(
            PaliWord.root_key, PaliWord.family_root).all()

    global root_family_list
    root_family_list = [(i.root_key, i.family_root, i.pali_root.root_meaning) for i in root_family_db]

    global dpd_db
    dpd_db = db_session.query(PaliWord).filter(
        PaliWord.family_root != "").order_by(
        PaliWord.root_key).all()
    dpd_db = sorted(
        dpd_db, key=lambda x: pali_sort_key(x.pali_1))

    global roots_db
    roots_db = db_session.query(PaliRoot).all()
    roots_db = sorted(
        roots_db, key=lambda x: pali_sort_key(x.root))

    global bases_dict
    bases_dict = {}


def generate_root_subfamily_html_and_extract_bases():
    print("[green]extracting bases and")
    print("[green]generating html for each root subfamily")

    add_to_db = []

    for counter, (root_key, subfamily, root_meaning) in enumerate(root_family_list):

        subfamily_db = db_session.query(PaliWord).filter(
            PaliWord.family_root == subfamily,
            PaliWord.root_key == root_key
            ).all()

        subfamily_db = sorted(
            subfamily_db, key=lambda x: pali_sort_key(x.pali_1))

        html_string = "<p class='heading underlined'>"
        if len(subfamily_db) == 1:
            html_string += f"<b>{len(subfamily_db)}</b> word belongs to the root family "
        else:
            html_string += f"<b>{len(subfamily_db)}</b> words belong to the root family "
        html_string += f"<b>{subfamily}</b> ({root_meaning})</p>"

        html_string += "<table class='family'>"

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

            meaning = make_meaning(i)

            html_string += f"<tr><th>{superscripter_uni(i.pali_1)}</th>"
            html_string += f"<td><b>{i.pos}</b></td>"
            html_string += f"<td>{meaning}</td></tr>"

        html_string += "</table>"

        root_family = FamilyRoot(
            root_id=root_key,
            root_family=subfamily,
            html=html_string,
            count=len(subfamily_db))

        add_to_db.append(root_family)

        if counter % 500 == 0:
            print(f"{counter:>10,} / {len(root_family_list):<10,} {subfamily}")
            with open(
                    f"xxx delete/root_subfamily/{i.family_root}.html", "w") as f:
                f.write(html_string)

    db_session.execute(FamilyRoot.__table__.delete())
    db_session.add_all(add_to_db)
    db_session.commit()


def root_grouper(root_group: int):

    root_groups = {
        1: "bh??v??diga???a",
        2: "rudh??diga???a",
        3: "div??diga???a",
        4: "sv??diga???a",
        5: "kiy??diga???a",
        6: "gah??diga???a",
        7: "tan??diga???a",
        8: "cur??diga???a"
    }
    return root_groups.get(root_group, "ERROR!")


def generate_root_info_html():
    print("[green]compiling root info")

    add_to_db = []

    for counter, i in enumerate(roots_db):

        root_clean = re.sub(" \\d*$", "", i.root)
        root_group_pali = root_grouper(i.root_group)
        try:
            bases = ", ".join(sorted(bases_dict[i.root], key=len))
        except KeyError:
            bases = "-"

        html_string = ""
        html_string += "<table class='root_info'><tbody>"
        html_string += f"<tr><th>P?????i Root:</th><td>{root_clean}"
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

        # Dh??tup??tha
        if i.dhatupatha_root != "-":
            html_string += "<tr><th>Dh??tup??tha:</th>"
            html_string += f"<td>{i.dhatupatha_root} <i>{i.dhatupatha_pali}"
            html_string += f"</i> ({i.dhatupatha_english}) "
            html_string += f"#{i.dhatupatha_num}</td></tr>"
        else:
            html_string += "<tr><th>Dh??tup??tha:</th><td>-</td></tr>"

        # Dh??tuma??j??sa
        if i.dhatumanjusa_root != "-":
            html_string += "<tr><th>Dh??tuma??j??sa:</th>"
            html_string += f"<td>{i.dhatumanjusa_root} "
            html_string += f"<i>{i.dhatumanjusa_pali}</i> "
            html_string += f"({i.dhatumanjusa_english}) "
            html_string += f"#{i.dhatumanjusa_num}</td></tr>"
        else:
            html_string += "<tr><th>Dh??tuma??j??sa:</th><td>-</td></tr>"

        # Saddan??ti
        if i.dhatumala_root != "-":
            html_string += "<tr><th>Saddan??ti:</th>"
            html_string += f"<td>{i.dhatumala_root} <i>{i.dhatumala_pali}</i> "
            html_string += f"({i.dhatumala_english})</td></tr>"
        else:
            html_string += "<tr><th>Saddan??ti:</th><td>-</td></tr>"

        # Sanskrit
        html_string += "<tr><th>Sanskrit Root:</th>"
        html_string += f"<td><span class='gray'>{i.sanskrit_root} "
        html_string += f"{i.sanskrit_root_class} "
        html_string += f"({i.sanskrit_root_meaning})</span></td></tr>"

        # P?????in??ya Dh??tup?????ha
        if i.panini_root != "-":
            html_string += "<tr><th>P?????in??ya Dh??tup?????ha:</th>"
            html_string += "<td><span class='gray'>"
            html_string += f"{i.panini_root} <i>{i.panini_sanskrit}</i> "
            html_string += f"({i.panini_english})</span></td></tr>"
        else:
            html_string += "<tr><th>P?????in??ya Dh??tup?????ha:</th><td>-</td></tr>"

        if i.note != "":
            html_string += f"<tr><th>Notes:</th><td>{i.note}</td></tr>"

        html_string += "</tbody></table>"

        count = db_session.query(PaliWord).filter(
            PaliWord.root_key == i.root).count()

        root_info = FamilyRoot(
            root_id=i.root,
            root_family="info",
            html=html_string,
            count=count
        )

        add_to_db.append(root_info)

        if counter % 100 == 0:
            print(
                f"{counter:>10,} / {len(roots_db):<10,} {i.root}")
            with open(f"xxx delete/root_info/{i.root}.html", "w") as f:
                f.write(html_string)

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
