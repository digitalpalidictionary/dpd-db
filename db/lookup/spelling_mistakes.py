#!/usr/bin/env python3

"""Add spelling mistakes to the lookup table."""

from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from tools.lookup_sync import sync_lookup_column
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv


@dataclass
class GlobalVars:
    pth: ProjectPaths
    db_session: Session
    spellings_dict: defaultdict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )


def load_spelling_dict(g: GlobalVars) -> None:
    """Turn the spelling_mistakes.tsv into a dictionary"""
    pr.green_tmr("loading spelling tsv")

    spellings_tsv = read_tsv(g.pth.spelling_mistakes_path)
    spellings_dict = defaultdict(set)
    for spelling, correction in spellings_tsv[1:]:
        spellings_dict[spelling].add(correction)
    g.spellings_dict = spellings_dict
    pr.yes(len(spellings_dict))


def add_spellings(g: GlobalVars) -> None:
    """Add/update the spelling column and clear stale entries."""
    pr.green_tmr("syncing spelling column")
    data = {
        mistake: pali_list_sorter(corrections)
        for mistake, corrections in g.spellings_dict.items()
    }
    result = sync_lookup_column(g.db_session, "spelling", data)
    pr.yes(result.updated + result.inserted)


def main() -> None:
    pr.tic()
    pr.yellow_title("add spelling mistakes to lookup table")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    g = GlobalVars(pth=pth, db_session=db_session)
    load_spelling_dict(g)
    add_spellings(g)
    g.db_session.commit()
    g.db_session.close()
    pr.toc()


if __name__ == "__main__":
    main()
