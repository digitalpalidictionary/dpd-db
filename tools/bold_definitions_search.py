#!/usr/bin/env python3

"""Search bold_defintions using vanilla find or regex."""

import re

from rich import print

from db.get_db_session import get_db_session
from db.models import BoldDefintion
from tools.paths import ProjectPaths


def search_bold_defintions(db, search1, search2):
    print("[green]search_bold_defintions_gui")
    is_regex = test_regex(search1, search2)
    if is_regex:
        search_results: list[BoldDefintion] = regex_search(db, search1, search2)
    else:
        search_results: list[BoldDefintion] = plain_search(db, search1, search2)
    print(f"{len(search_results)} reults found")
    return search_results

   
def test_regex(search1, search2) -> bool:
    print("test regex ", end="")
    regex_characters = [
        "\\+", "\\*", "|", "\\.", "\\/", "\\[", "\\]", "\\(", "\\)", "$", "^"]
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


def regex_search(db, search1, search2) -> list[BoldDefintion]:
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


def plain_search(db, search1, search2) -> list[BoldDefintion]:
    print("plain search")
    search_results = []
    for i in db:
        if search1 in i.bold and search2 in i.commentary:
            search_results.append(i)
    return search_results


if __name__ == "__main__":
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(BoldDefintion).all()
    bold_defintions_db = db_session.query(BoldDefintion).all()
    search1 = "dantadh.*"
    search2 = "ñ*"
    search_results = search_bold_defintions_gui(bold_defintions_db, search1, search2)

