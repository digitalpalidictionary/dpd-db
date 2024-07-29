"""Find all the nuns names in Therigāthā."""

import csv
import re

from typing import Tuple, List
from rich import print
from tools.paths import ProjectPaths
from tools.cst_source_sutta_example import make_cst_soup



def find_names_and_number():
    pth = ProjectPaths()
    book = "kn9"
    soup = make_cst_soup(pth, book, unwrap_notes=False)

    sutta_counter = 0
    chapter_number = 0
    chapter_counter = 0
    verse = 1

    name_list: List[Tuple[str, int, str, int]] = []

    heads = soup.find_all('head', {'rend': 'chapter'})
    for head in heads:
        chapter_number += 1
        chapter_counter = 0

        ps = head.find_next_siblings('p')
        for p in ps:

            first_verse_flag = True 

            # paragraph number
            if (
                p["rend"] == "hangnum"
                and first_verse_flag
            ):
                verse = int(p["n"]) + 1
                first_verse_flag = False

            # find name in heading
            if p["rend"] == "subhead":
                sutta_counter += 1
                chapter_counter += 1

                # remove digits fullstop
                name = re.sub(r"\d*\. ", "", p.text)
                if "therīgāthā" in p.text:
                    name = re.sub("therīgāthā", "", name)

                name = name_cleaner(name)
                name_list.append((
                    name, sutta_counter,
                    f"{chapter_number}.{chapter_counter}", verse))
            
            if (
                p["rend"] == "bodytext" or
                p["rend"] == "centre"
            ):
                # find names with " therī" in them
                if " therī" in p.text:

                    # find names inside notes
                    note = p.find("note")
                    if note:
                        name = note.text
                        if name is not None:
                            name = re.sub(r" \(.*\)", "", name)
                            name = name_cleaner(name)
                            name_list.append((
                                    name, sutta_counter,
                                    f"{chapter_number}.{chapter_counter}", verse))
                        note.decompose()

                    # find the word before "therī"
                    name = p.text.split("therī")[0].split()[-1]
                    name = name_cleaner(name)
                    name_list.append((
                        name, sutta_counter,
                        f"{chapter_number}.{chapter_counter}", verse))
    
    return name_list


def test_missing_numbers(name_list):
    has_number = set()
    for i in name_list:
        name, number, chapter, verse = i
        has_number.add(number)
    
    for i in range(1, 73):
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
    if re.match(r"\d", name):
        name = re.sub(r"\d\.", "", name)
    # remove digits
    if re.match(r"\d", name):
        name = re.sub(r"\d", "", name)
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
    for counter, i in enumerate(name_list):
        name, sutta_number, chapter, verse = i
        if sutta_number not in dict:
            dict[sutta_number] = {
                "chapter": chapter,
                "first_verse": verse,
                "last_verse": verse,
                "name":{name}}
        else:
            dict[sutta_number]["name"].add(name)
            dict[sutta_number]["last_verse"] = verse-1
    return dict

def write_tsv(name_dict):
    with open("temp/theris.tsv", "w") as f:
        writer = csv.writer(f, delimiter="\t")
        header = ["add", "lemma_1", "lemma_2", "pos", "grammar", "meaning_1", "variant", "notes", "family_set", "stem", "pattern\n"]
        writer.writerow(header)
        for number, i in name_dict.items():
            chapter = i["chapter"]
            first_verse = i["first_verse"]
            last_verse = i["last_verse"]
            if first_verse == last_verse:
                verses = f"verse {first_verse}"
                note_ending = "is attributed to her"
            else:
                verses = f"verses {first_verse}-{last_verse}"
                note_ending = "are attributed to her"
            names = i["name"]
            for name in names:
                lemma_1, lemma_2, stem, pattern = name_stem_pattern(name)
                add = ""
                pos = "fem"
                grammar = "fem"
                meaning_1 = "name of an arahant nun"
                variant = f"{', '.join(names - {name})}"
                variant = variant_replacer(variant)
                notes = f"Therīgāthā {verses} (TH{chapter}, TH{number}) {note_ending}."
                family_set = "names of nuns; names of arahants"
                data = [add, lemma_1, lemma_2, pos, grammar, meaning_1, variant, notes, family_set, stem, pattern]
                writer.writerow(data)

def variant_replacer(name):
    if "dhītu" in name:
        name = name.replace("dhītu", "dhītar")
    elif "dhītā" in name:
        name = name.replace("dhītā", "dhītar")
    elif "mātā" in name:
        name = name.replace("mātā", "mātar")
    elif "mātu" in name:
        name = name.replace("mātu", "mātar")   
    return name   



def name_stem_pattern(name):
    if name.endswith("dhītā"):
        lemma_1 = name.replace("dhītā", "dhītar")
        lemma_2 = name
        stem = name[:-1]
        pattern = "ar fem"
    elif name.endswith("dhītu"):
        lemma_1 = name.replace("dhītu", "dhītar")
        lemma_2 = name.replace("dhītu", "dhītā")
        stem = name[:-1]
        pattern = "ar fem"
    elif name.endswith("mātā"):
        lemma_1 = name.replace("mātā", "mātar")
        lemma_2 = name
        stem = name[:-4]
        pattern = "mātar fem"
    elif name.endswith("mātu"):
        lemma_1 = name.replace("mātu", "mātar")
        lemma_2 = name.replace("mātu", "mātā")
        stem = name[:-4]
        pattern = "mātar fem"
    else:
        lemma_1 = name
        lemma_2 = name
        stem = name[:-1]
        pattern = f"{name[-1]} fem"
    return lemma_1, lemma_2, stem, pattern
    


def make_lemma_2(name):
    if name.endswith("a"):
        name = f"{name[:-1]}o"
    return name    


if __name__ == "__main__":
    name_list = find_names_and_number()
    test_missing_numbers(name_list)
    name_list = reduce_list(name_list)
    name_dict = sutta_chapter_name_dict(name_list)
    write_tsv(name_dict)
    # print(name_dict)
    
