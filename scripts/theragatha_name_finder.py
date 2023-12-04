import re

from typing import Tuple, List
from rich import print
from tools.paths import ProjectPaths
from tools.source_sutta_example import make_cst_soup


def find_names_and_number():
    pth = ProjectPaths()
    book = "kn8"
    soup = make_cst_soup(pth, book, unwrap_notes=False)

    sutta_counter = 0
    chapter_number = 0
    chapter_counter = 0

    name_list: List[Tuple[str, int, str]] = []

    heads = soup.find_all('head', {'rend': 'chapter'})
    for head in heads:
        chapter_number += 1
        chapter_counter = 0

        ps = head.find_next_siblings('p')
        for p in ps:

            # find name in heading
            if p["rend"] == "subhead":
                sutta_counter += 1
                chapter_counter += 1

                name = re.sub(r"\d*\. ", "", p.text)
                if "theragāthā" in p.text:
                    name = re.sub("ttheragāthā", "", name)
                elif "sāmaṇeragāthā" in p.text:
                    name = re.sub("sāmaṇeragāthā", "", name)\

                name = name_cleaner(name)
                name_list.append(
                    (name, sutta_counter, f"{chapter_number}.{chapter_counter}"))


            
            if (
                p["rend"] == "bodytext" or
                p["rend"] == "centre"
            ):
                # find names with "tthero" in them
                if "tthero" in p.text:
                    name = re.findall(
                        r"\b[^ ]*tthero\b", p.text)[0]
                    if name:
                        name = name_cleaner(name)
                    name_list.append(   
                        (name, sutta_counter, f"{chapter_number}.{chapter_counter}"))
                
                # find names with " thero" in them
                if " thero" in p.text:

                    # find names inside notes
                    note = p.find("note")
                    if note:
                        name = note.text
                        if name is not None:
                            name = re.sub(r" \(.*\)", "", name)
                            name = name_cleaner(name)
                            name_list.append(
                                (name, sutta_counter, f"{chapter_number}.{chapter_counter}"))
                        note.decompose()

                    # find the word before "thero"
                    name = p.text.split("thero")[0].split()[-1]
                    name = name_cleaner(name)
                    name_list.append(
                        (name, sutta_counter, f"{chapter_number}.{chapter_counter}"))
    
    return name_list


def test_missing_numbers(name_list):
    has_number = set()
    for i in name_list:
        name, number, chapter = i
        has_number.add(number)
    
    for i in range(1, 264):
        if i not in has_number:
            print(i)


def name_cleaner(name):
    # remove brackets
    if "(" in name:
        name = re.sub(".+-", "", name)
    # replace masc o
    if name.endswith("o"):
        name = f"{name[:-1]}a"
    # remove …
    if "…" in name:
        name = name.replace("…", "")
    # remove digits fullstop
    if re.match(r"\d", name):
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
    dict = {}
    for name, sutta_number, chapter in name_list:
        if sutta_number not in dict:
            dict[sutta_number] = {
                "chapter": chapter,
                "name":[name]}
        else:
            dict[sutta_number]["name"].append(name)
    return dict


if __name__ == "__main__":
    name_list = find_names_and_number()
    name_list = reduce_list(name_list)
    name_dict = sutta_chapter_name_dict(name_list)
    print(name_dict)
    test_missing_numbers(name_list)

