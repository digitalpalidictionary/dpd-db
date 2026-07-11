#!/usr/bin/env python3

"""Find words starting with 'su + ' in construction and check they are kammadhāraya."""

import json

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def load_exceptions(pth: ProjectPaths) -> list[int]:
    """Load exception IDs from the JSON file alongside this script."""
    if pth.su_kammadharaya_exceptions_path.exists():
        with open(pth.su_kammadharaya_exceptions_path, encoding="utf-8") as f:
            return json.load(f)
    return []


def main() -> None:
    pr.tic()
    print("[bright_yellow]find su- words that are not kammadhāraya")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    exceptions = load_exceptions(pth)

    counter = 0
    for i in db:
        if (
            i.construction
            and i.construction.startswith("su + ")
            and "kammadhāraya" not in (i.compound_type or "")
            and i.id not in exceptions
        ):
            print(f"[magenta1]{i.lemma_1} {i.pos}")
            print(f"[indian_red]{i.meaning_combo}")
            print(f"[hot_pink]{i.construction}")
            counter += 1

    pr.summary("total", counter)
    pr.toc()


if __name__ == "__main__":
    main()
