"""Add all the sutta codes to the lookup table referring to the original sutta(s)."""

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup, SuttaInfo
from tools.configger import config_read
from tools.lookup_is_another_value import is_another_value
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.sutta_codes import make_list_of_sutta_codes
from tools.update_test_add import update_test_add

SuttaInfoDict = dict[str, set[int]]


@dataclass
class GlobalVars:
    pth: ProjectPaths
    db_session: Session
    sutta_db: list[SuttaInfo]
    lookup_db: list[Lookup]
    sutta_info_dict: SuttaInfoDict = field(default_factory=dict)


def make_sutta_info_dict(g: GlobalVars) -> None:
    pr.green_tmr("make sutta info dict")

    name_to_id: dict[str, int] = {
        lemma: hw_id
        for lemma, hw_id in g.db_session.query(DpdHeadword.lemma_1, DpdHeadword.id)
        .filter(DpdHeadword.lemma_1.in_([su.dpd_sutta for su in g.sutta_db]))
        .all()
    }

    for su in g.sutta_db:
        sutta_id = name_to_id.get(su.dpd_sutta)
        if sutta_id is None:
            pr.red(f"error: '{su.dpd_sutta}'")
            continue
        for code in make_list_of_sutta_codes(su):
            g.sutta_info_dict.setdefault(code, set()).add(sutta_id)

    pr.yes(len(g.sutta_info_dict))


def add_to_lookup_table(g: GlobalVars) -> None:
    """Add sutta info to lookup table."""

    pr.green_title("saving to Lookup table")
    pr.white_tmr("update test or add")

    update_set, test_set, add_set = update_test_add(g.lookup_db, g.sutta_info_dict)
    pr.yes("")

    pr.white_tmr("updating and deleting")
    for i in g.lookup_db:
        if i.lookup_key in update_set:
            i.headwords_pack(list(g.sutta_info_dict[i.lookup_key]))
        elif i.lookup_key in test_set:
            if not is_another_value(i, "headwords") and not i.headwords:
                g.db_session.delete(i)
    pr.yes(len(update_set))

    pr.white_tmr("adding")
    add_to_db = []
    for key, data in g.sutta_info_dict.items():
        if key in add_set:
            add_me = Lookup()
            add_me.lookup_key = key
            add_me.headwords_pack(list(data))
            add_to_db.append(add_me)
    pr.yes(len(add_set))

    pr.white_tmr("committing")
    g.db_session.add_all(add_to_db)
    g.db_session.commit()
    pr.yes("ok")


def main() -> None:
    pr.tic()
    pr.yellow_title("add sutta codes to lookup table")
    if config_read("generate", "suttas", "yes") == "no":
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    g = GlobalVars(
        pth,
        db_session,
        db_session.query(SuttaInfo).all(),
        db_session.query(Lookup).all(),
    )
    make_sutta_info_dict(g)
    add_to_lookup_table(g)
    pr.toc()


if __name__ == "__main__":
    main()
