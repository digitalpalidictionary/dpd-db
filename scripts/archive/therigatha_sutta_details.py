""" "Find names, chapters and verses of Therīgātha titles,
and update current names in db"""

import re

from typing import Tuple, List
from rich import print
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.cst_source_sutta_example import make_cst_soup
from tools.tsv_read_write import dotdict


def find_names_and_number():
    pth = ProjectPaths()
    book = "kn9"
    soup = make_cst_soup(pth, book, unwrap_notes=False)

    sutta_counter = 0
    chapter_number = 0
    chapter_counter = 0
    verse = 1

    name_list: List[Tuple[str, int, str, int]] = []

    heads = soup.find_all("head", {"rend": "chapter"})
    for head in heads:
        chapter_number += 1
        chapter_counter = 0

        ps = head.find_next_siblings("p")
        for p in ps:
            first_verse_flag = True

            # paragraph number
            if p["rend"] == "hangnum" and first_verse_flag:
                verse = int(p["n"]) + 1
                first_verse_flag = False

            # find name in heading
            if p["rend"] == "subhead":
                sutta_counter += 1
                chapter_counter += 1

                # remove digits fullstop
                name = re.sub(r"\d*\. ", "", p.text)
                name = name_cleaner(name)
                name_list.append(
                    (name, sutta_counter, f"{chapter_number}.{chapter_counter}", verse)
                )

    return name_list


def test_missing_numbers(name_list):
    has_number = set()
    for i in name_list:
        name, number, chapter, verse = i
        has_number.add(number)

    for i in range(1, 74):
        if i not in has_number:
            print(i)


def name_cleaner(name):
    # remove brackets
    if "(" in name:
        name = re.sub(".+-", "", name)
    # remove …
    if "…" in name:
        name = name.replace("…", "")
    # remove digits fullstop
    if re.match(r"\d\.", name):
        name = re.sub(r"\d\.", "", name)
    # lowercase
    return name.lower()


def reduce_list(name_list):
    seen_list = list()
    for i in name_list:
        if i not in seen_list:
            seen_list.append(i)
    return seen_list


def sutta_chapter_name_dict(name_list):
    # find all the duplicate names
    multiples = {}
    seen = set()
    for i in name_list:
        name, sutta_number, chapter, verse = i
        if name in seen:
            multiples.update({name: 0})
        else:
            seen.add(name)

    dict = {}
    previous_name = None
    for i in name_list:
        name, sutta_number, chapter, verse = i
        # increment the number
        if name in multiples:
            multiples[name] += 1
            name = f"{name} {multiples[name]}"

        dict[name] = {
            "sutta": sutta_number,
            "chapter": chapter,
            "first_verse": verse,
            "last_verse": 0,
        }

        if previous_name:
            dict[previous_name]["last_verse"] = verse - 1
        if name == "sumedhātherīgāthā":
            dict[name]["last_verse"] = 524
        previous_name = name

    return dict


def add_to_db(name_dict):
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    count = 1
    test_set = set()
    for i in db:
        if i.lemma_1 in name_dict:
            print(i.lemma_1)
            print(i.meaning_2)
            x = dotdict(name_dict[i.lemma_1])
            string = f"Therīgāthā {x.sutta}, "
            string += f"chapter {x.chapter}, "
            if x.first_verse == x.last_verse:
                string += f"verse {x.first_verse} "
            else:
                string += f"verses {x.first_verse}-{x.last_verse} "
            string += f"(THI{x.sutta})"
            print(string)
            print()
            count += 1
            i.meaning_2 = string
            test_set.add(x.sutta)
        else:
            if "aññataratherīgāthā" in i.lemma_1:
                print(f"[red]{i.lemma_1} not added")

    db_session.commit()
    print(count)

    for i in range(1, 73):
        if i not in test_set:
            print(f"[red]{i} missing")


if __name__ == "__main__":
    name_list = find_names_and_number()
    test_missing_numbers(name_list)
    name_list = reduce_list(name_list)
    # print(name_list)
    # print(len(name_list))
    name_dict = sutta_chapter_name_dict(name_list)
    print(name_dict)
    add_to_db(name_dict)
