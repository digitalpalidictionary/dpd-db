"""Add all the sutta codes to the lookup table referring to the original sutta(s)."""

import re
from dataclasses import dataclass, field

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup, SuttaInfo
from tools.lookup_is_another_value import is_another_value
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.update_test_add import update_test_add

SuttaInfoDict = dict[str, set[int]]


@dataclass
class GlobalVars:
    pth: ProjectPaths = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    sutta_db = db_session.query(SuttaInfo).all()
    lookup_db = db_session.query(Lookup).all()
    sutta_info_dict: SuttaInfoDict = field(default_factory=dict)
    sutta_code: str = field(default_factory=str)
    sutta_name: str = field(default_factory=str)
    sutta_id: int = field(default_factory=int)


def make_list_of_sutta_codes(code_with_dash: str) -> list[str]:
    # find the base of the code, 'SN12.' in 'SN12.5-8'
    code_base = re.sub(r"(?<=\.).+", "", code_with_dash)
    # find the part with dashes, '5-8.' in 'SN12.5-8'
    code_dash = re.sub(code_base, "", code_with_dash)
    # find the first digit, 5 in 'SN12.5-8'
    code_first = int(re.sub(r"-.+", "", code_dash))
    # find the last digit, 8 in 'SN12.5-8'
    code_last = int(re.sub(r".+-", "", code_dash))

    sutta_code_list = []
    for num in range(code_first, code_last + 1):
        sutta_code_list.append(f"{code_base}{num}")
        # print(code_with_dash, f"{code_base}{num}")
    return sutta_code_list


def add_code_to_dict(
    g: GlobalVars,
) -> None:
    if g.sutta_code not in g.sutta_info_dict:
        g.sutta_info_dict[g.sutta_code] = set([g.sutta_id])
    else:
        g.sutta_info_dict[g.sutta_code].add(g.sutta_id)


def get_id(g: GlobalVars):
    id = (
        g.db_session.query(DpdHeadword.id)
        .filter(DpdHeadword.lemma_1 == g.sutta_name)
        .first()
    )
    if id:
        g.sutta_id = id[0]
    else:
        pr.red(g.sutta_name)


def make_sutta_info_dict(g: GlobalVars):
    pr.green("make sutta info dict")
    for i in g.sutta_db:
        g.sutta_name = i.dpd_sutta
        g.sutta_code = i.dpd_code
        get_id(g)

        if i.dpd_code:
            add_code_to_dict(g)

            if "-" in i.dpd_code:
                sutta_codes = make_list_of_sutta_codes(i.dpd_code)
                for code in sutta_codes:
                    g.sutta_code = code
                    add_code_to_dict(g)

        if i.sc_code:
            g.sutta_code = i.sc_code.upper()
            add_code_to_dict(g)

            if "-" in i.sc_code:
                sutta_codes = make_list_of_sutta_codes(i.sc_code.upper())
                for code in sutta_codes:
                    g.sutta_code = code
                    add_code_to_dict(g)

    pr.yes(len(g.sutta_info_dict))


def add_to_lookup_table(g: GlobalVars) -> None:
    """Add sutta info to lookup table."""

    pr.green_title("saving to Lookup table")
    pr.white("update test or add")

    results = update_test_add(g.lookup_db, g.sutta_info_dict)
    update_set, test_set, add_set = results
    pr.yes("")

    pr.white("updating and deleting")
    # update test add
    for i in g.lookup_db:
        if i.lookup_key in update_set:
            i.headwords_pack(list(g.sutta_info_dict[i.lookup_key]))
        elif i.lookup_key in test_set:
            if is_another_value(i, "headwords"):
                # i.headwords_pack([])
                pass
            else:
                g.db_session.delete(i)
    pr.yes(len(update_set))

    pr.white("adding")
    # add
    add_to_db = []
    for key, data in g.sutta_info_dict.items():
        if key in add_set:
            add_me = Lookup()
            add_me.lookup_key = key
            add_me.headwords_pack(list(data))
            add_to_db.append(add_me)
    pr.yes(len(add_set))

    pr.white("committing")
    g.db_session.add_all(add_to_db)
    g.db_session.commit()
    pr.yes("ok")


def print_results(g: GlobalVars) -> None:
    for key, value in g.sutta_info_dict.items():
        if len(value) > 1:
            print(key, value)


def main() -> None:
    pr.tic()
    pr.title("add sutta codes to lookup table")
    g: GlobalVars = GlobalVars()
    make_sutta_info_dict(g)
    # print_results(g)
    add_to_lookup_table(g)
    pr.toc()


if __name__ == "__main__":
    main()
