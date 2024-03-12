#!/usr/bin/env python3

import json
import re

from bs4 import BeautifulSoup
from rich import print

from db.models import BoldDefintion
from db.get_db_session import get_db_session

from db.bold_defintions.functions import useless_endings
from db.bold_defintions.functions import file_list
from db.bold_defintions.functions import defintion_to_dict
from db.bold_defintions.functions import dissolve_empty_siblings
from db.bold_defintions.functions import get_nikaya_headings_div
from db.bold_defintions.functions import get_headings_no_div
from db.bold_defintions.functions import get_bold_strings

from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.tsv_read_write import write_tsv_dot_dict


def main():
    tic()
    print("[bright_yellow]building database of bolded defintions")
    
    pth = ProjectPaths()
    bold_defintions = extract_bold_definitions(pth)
    update_db(pth, bold_defintions)
    export_json(pth, bold_defintions)
    toc()


def debugger(para, bold):
    print(f"{'para':<40}{para}")
    print(f"{'bold':<40}{para}")
    print(f"{'bold.next_sibling':<40}{bold.next_sibling}")
    print(f"{'bold.next_sibling.next_sibling':<40}{bold.next_sibling.next_sibling}")


def extract_bold_definitions(pth):
    """extract commentary definitions from xml."""

    bold_definitions_list = []

    # log_file = "log/log.tsv"
    # log = open (log_file, "a")

    bold_total = 0

    for file_name, ref_code in file_list.items():
        print(f"{file_name}\t{ref_code}", end="\t")
        # log.write(f"\t{file_name}\t{ref_code}\t")

        bold_count1 = 0
        bold_count2 = 0
        no_meaning_count = 0
        nikaya, book, title, subhead = ["", "", "", ""]
        
        # open xml file
        with open(pth.cst_xml_roman_dir.joinpath(file_name), "r", 
            encoding="UTF-16") as file:
            xml = file.read()
        
        # make the soup
        soup = BeautifulSoup(xml, "xml")
        
        # remove all the "pb" tags
        pbs = soup.find_all("pb")
        for pb in pbs:
            pb.decompose()

        # remove all the notes
        notes = soup.find_all("note")
        for note in notes:
            note.decompose()

        # remove all the hi parunum dot tags
        his = soup.find_all("hi", rend=["paranum", "dot"])
        for hi in his:
            hi.unwrap()

        # grab the number of bolds
        bold_count1 = len(soup.find_all("hi", rend="bold"))
        
        # grab the headings for suttas pitaka
        if soup.div is not None:
            print("has div", end="\t")
            # log.write("has div\t")

            nikaya = soup.find_all("p", rend="nikaya")[0].string
            book = soup.find_all("head", rend="book")[0].string

            divs = soup.find_all("div", type=["sutta", "vagga", "chapter", "samyutta", "kanda", "khandaka"])

            # no real divs in anguttara ṭīkā
            ant = ["s0401t.tik.xml", "s0402t.tik.xml", "s0403t.tik.xml", "s0404t.tik.xml"]
            if file_name in ant:
                divs = soup.find_all("div", type=["book"])

            for div in divs:
                paras = div.find_all("p")

                for para in paras:
                    title, subhead = get_nikaya_headings_div(
                        file_name, div, para, subhead)
                    
                    bolds = para.find_all("hi", rend=["bold"])
                    bolds = dissolve_empty_siblings(para, bolds)
                    
                    for bold in bolds:
                        if bold.next_sibling is not None:
                            bold, bold_e, bold_comp, bold_n = get_bold_strings(bold)
                            
                            # only write substantial examples
                            bold_comp_clean = re.sub("\\<b\\>|\\</b\\>", "", bold_comp)
                            if f"{bold}{bold_e}" == bold_comp_clean.strip():
                                no_meaning_count +=1
                            elif bold_n in useless_endings:
                                no_meaning_count += 1
                                continue
                            else:
                                bold_definitions_list += [defintion_to_dict(
                                    file_name, ref_code, nikaya, book, 
                                    title, subhead, bold, bold_e, 
                                    bold_comp)]
                                bold_count2 += 1

            print(f"{bold_count1}\t{bold_count2}\t{no_meaning_count}")
            # log.write(f"{bold_count1}\t{bold_count2}\t{no_meaning_count}\n")

            bold_total += bold_count2
                                
        # for vinaya, khuddaka nikaya, vism
        elif soup.div is None:
            print("no div", end="\t")
            # log.write("no div\t")

            paras = soup.find_all("p")

            for para in paras:
                nikaya, book, title, subhead = get_headings_no_div(para, file_name, nikaya, book, title, subhead)
                
                bolds = para.find_all("hi", rend="bold")
                bolds = dissolve_empty_siblings(para, bolds)

                for bold in bolds:
                    if bold.next_sibling is not None:
                        bold, bold_e, bold_comp, bold_n  = get_bold_strings(bold)

                        # only write substantial examples
                        bold_comp_clean = re.sub("\\<b\\>|\\</b\\>", "", bold_comp)
                        if f"{bold}{bold_e}" == bold_comp:
                            no_meaning_count += 1
                        elif bold_n in useless_endings:
                            no_meaning_count += 1
                            continue
                        else:
                            bold_definitions_list += [defintion_to_dict(
                                    file_name, ref_code, nikaya, book, 
                                    title, subhead, bold, bold_e, 
                                    bold_comp)]
                            bold_count2 += 1
    
            print(f"{bold_count1}\t{bold_count2}\t{no_meaning_count}")
            # log.write(f"{bold_count1}\t{bold_count2}\t{no_meaning_count}\n")
            bold_total+= bold_count2
    
    print(f"bold_total {bold_total}")
    # log.close()

    return bold_definitions_list


def export_json(pth, bold_defintions_list):
    """convert to tsv and json for rebuilding the db and external use."""

    file_path = pth.bold_defintions_tsv_path
    write_tsv_dot_dict(file_path, bold_defintions_list)

    file_path = pth.bold_defintions_json_path
    with open(file_path, "w") as file:
        json.dump(bold_defintions_list, file)

    print("[white]ok")


def update_db(pth, bold_defintions):
    """Add bold defintions to dpd.db."""

    print("[green]adding defintions to db")
    db_session = get_db_session(pth.dpd_db_path)
    add_to_db = []

    for i in bold_defintions:
        bd = BoldDefintion()
        bd.update_bold_defintion(
            i["file_name"],
            i["ref_code"],
            i["nikaya"],
            i["book"],
            i["title"],
            i["subhead"],
            i["bold"],
            i["bold_end"],
            i["commentary"])
        
        add_to_db.append(bd)
    
    db_session.execute(BoldDefintion.__table__.delete()) # type: ignore
    db_session.add_all(add_to_db)
    db_session.commit()


if __name__ == "__main__":
    main()

    # TODO data
    # check what's not getting written
    # remove space comma
    # why no </b> tag?
    # bold ends with '
    # delete dupes
    # <b>diṭṭhivisuddhi</b> <b>kho panā</b>
    
    # bold is empty
    # bold starts with space
    # bold = <hi rend="bold"/>
    # bold ends with .
    # bold ends with '
    # bold = ,
    # replace ...pe with ' ... '
    # ends with bold not being added

    # TODO code
    # add to gui, other places?
    # automatically update html script
    # combine file names & book names with CST books

    # TESTS
    # last letter of bold /W

