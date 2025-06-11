#!/usr/bin/env python3

"""Quick starter template for getting a database session and iterating thru."""

from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    pth: ProjectPaths = ProjectPaths()
    db_session: Session = get_db_session(pth.dpd_db_path)

    # Query all origin values
    # Each item in origin_values_query will be a tuple, e.g., ('Sk',), or (None,)
    origin_values_query: list = db_session.query(DpdHeadword.origin).distinct().all()

    # Extract origin strings from the tuples, handling potential None values
    all_origins: list[str | None] = [item[0] for item in origin_values_query if item]

    # Get unique origin values, filtering out None if they are not considered a distinct category
    unique_origins: set[str] = {origin for origin in all_origins if origin is not None}

    pr.green("Unique values in DpdHeadword.origin:")
    for origin_value in sorted(list(unique_origins)):
        pr.info(origin_value)


if __name__ == "__main__":
    main()
