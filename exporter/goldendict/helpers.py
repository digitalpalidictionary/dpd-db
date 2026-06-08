"""A few helpful lists and functions for the exporter."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from db.models import DpdHeadword
from tools.date_and_time import now

TODAY = now.date()


def make_roots_count_dict(db_session: Session) -> dict[str, int]:
    rows = (
        db_session.query(DpdHeadword.root_key, func.count())
        .filter(DpdHeadword.root_key.is_not(None))
        .group_by(DpdHeadword.root_key)
        .all()
    )
    return {root_key: count for root_key, count in rows}
