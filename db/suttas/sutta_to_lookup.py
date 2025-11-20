"""Add all the sutta codes to the lookup table referring to the original sutta(s)."""

from dataclasses import dataclass, field

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup, SuttaInfo
from tools.lookup_is_another_value import is_another_value
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.sutta_codes import make_list_of_sutta_codes
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


def add_code_to_dict(
    g: GlobalVars,
) -> None:
    if g.sutta_code not in g.sutta_info_dict:
        g.sutta_info_dict[g.sutta_code] = set([g.sutta_id])
    else:
        g.sutta_info_dict[g.sutta_code].add(g.sutta_id)


def get_id(g: GlobalVars):
    """Needs sutta_name"""

    if g.sutta_name:
        id = (
            g.db_session.query(DpdHeadword.id)
            .filter(DpdHeadword.lemma_1 == g.sutta_name)
            .first()
        )
        if id:
            g.sutta_id = id[0]
        else:
            pr.red(f"error: '{g.sutta_name}'")
    else:
        pr.red(f"error: '{g.sutta_name}'")


def make_sutta_info_dict(g: GlobalVars):
    pr.green("make sutta info dict")
    for su in g.sutta_db:
        g.sutta_name = su.dpd_sutta
        get_id(g)
        sutta_codes = make_list_of_sutta_codes(su)
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
    add_to_lookup_table(g)
    pr.toc()


if __name__ == "__main__":
    main()
