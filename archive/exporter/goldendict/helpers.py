"""A few helpful lists and functions for the exporter."""

from typing import Dict
from datetime import date

from sqlalchemy.orm import Session

from db.models import DpdHeadword

TODAY = date.today()

EXCLUDE_FROM_SETS: set = {"dps", "ncped", "pass1", "sandhi"}


def make_roots_count_dict(db_session: Session) -> Dict[str, int]:
    roots_db = db_session.query(DpdHeadword).all()
    roots_count_dict: Dict[str, int] = dict()
    for i in roots_db:
        if i.root_key is None:
            continue
        if i.root_key in roots_count_dict:
            roots_count_dict[i.root_key] += 1
        else:
            roots_count_dict[i.root_key] = 1

    return roots_count_dict
