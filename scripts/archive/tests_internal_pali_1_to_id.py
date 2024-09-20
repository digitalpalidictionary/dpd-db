#!/usr/bin/env python3

"""Convert lemma_1 to id in internal tests."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths

from gui.functions_tests import make_internal_tests_list
from gui.functions_tests import write_internal_tests_list

class ProgData():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    pali_to_id_dict: dict
    internal_tests_list: list

g = ProgData()


def make_pali_to_id_dict():
    pali_to_id_dict = {}
    for i in g.db:
        pali_to_id_dict[i.lemma_1] = i.id
    g.pali_to_id_dict = pali_to_id_dict


def main():
    make_pali_to_id_dict()
    g.internal_tests_list = make_internal_tests_list(g.pth)
    for i in g.internal_tests_list:
        exceptions_ids = []
        for exception in i.exceptions:            
            exception_id = g.pali_to_id_dict.get(exception, None)
            
            if exception_id:
                exceptions_ids.append(exception_id)
            else:
                print(exception, end=" > ")
                print(exception_id)
        
        print(f"{i.test_name:<30}", end="")
        print(i.exceptions)
        print(f"{i.test_name:<30}", end="")
        i.exceptions = exceptions_ids
        print(i.exceptions)

    write_internal_tests_list(g.pth, g.internal_tests_list)









if __name__ == "__main__":
    main()
