"""Add all the sutta codes to the lookup table referring to the original sutta(s).

NOTE — ordering dependency
This script is purely additive (``clear_stale=False``).  It relies on
``db/inflections/inflections_to_headwords.py`` (build order 47) running
*immediately before* it (build order 50) with ``clear_stale=True``.
Inflections clears every non-inflection ``headwords`` row first — including
last build's sutta codes — so only current codes survive.

A standalone run of this script (without inflections clearing first) will
accumulate stale sutta codes over multiple builds.  Do not change the build
order without revisiting this constraint.
"""

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, SuttaInfo
from tools.configger import config_read
from tools.lookup_sync import sync_lookup_column
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.sutta_codes import make_list_of_sutta_codes

SuttaInfoDict = dict[str, set[int]]


@dataclass
class GlobalVars:
    pth: ProjectPaths
    db_session: Session
    sutta_db: list[SuttaInfo]
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
    pr.white_tmr("sync lookup column")
    data = {code: sorted(ids) for code, ids in g.sutta_info_dict.items()}
    result = sync_lookup_column(g.db_session, "headwords", data, clear_stale=False)
    pr.yes(result.updated + result.inserted)


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
    )
    make_sutta_info_dict(g)
    add_to_lookup_table(g)
    pr.toc()


if __name__ == "__main__":
    main()
