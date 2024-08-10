#!/usr/bin/env python3

"""Search bold_definitions using vanilla find or regex."""

import re

from rich import print

from db.db_helpers import get_db_session
from db.models import BoldDefinition
from tools.paths import ProjectPaths


def search_bold_definitions(db_session, search1, search2):
    print("[green]search_bold_definitions_gui")

    # remove problem characters
    if search1.endswith("\\"):
        search1 = search1.replace("\\", "")
    if search2.endswith("\\"):
        search2 = search2.replace("\\", "")
    
    search_results = db_session \
        .query(BoldDefinition) \
        .filter(BoldDefinition.bold.regexp_match(search1)) \
        .filter(BoldDefinition.commentary.regexp_match(search2)) \
        .all()
    
    print(f"{len(search_results)} results found")
    return search_results

   
def test_regex(search1, search2) -> bool:
    print("test regex ", end="")
    # regex_characters = re.escape("+*|./[]()$^")
    regex_characters = [
        "\\+", "\\*", "\\|", "\\.", "\\[", "\\]", "\\(", "\\)", "\\$", "\\^"]
    regex_str = "|".join(regex_characters)

    if re.findall(regex_str, search1):
        print(True)
        return True
    elif re.findall(regex_str, search2):
        print(True)
        return True
    else:
        print(False)
        return False


def regex_search(db, search1, search2) -> list[BoldDefinition]:
    print("regex_search")

    search_results = []
    for i in db:
        try:
            if (
                re.findall(search1, i.bold)
                and re.findall(search2, i.commentary)
            ):
                search_results.append(i)
        except re.error as e:
            print(f"[red]{e}")
            break
    return search_results


def plain_search(db, search1, search2) -> list[BoldDefinition]:
    print("plain search")
    search_results = []
    for i in db:
        if search1 in i.bold and search2 in i.commentary:
            search_results.append(i)
    return search_results


if __name__ == "__main__":
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    search1 = input("enter search1: ")
    search2 = input("enter search2: ")
    search_results = search_bold_definitions(db_session, search1, search2)

