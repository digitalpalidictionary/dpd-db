#!/usr/bin/env python3

"""
Template for quickly getting a database session and iterating over headwords.
"""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main() -> None:
    """Print the lemma of every headword that has sutta info attached."""
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    headwords = db_session.query(DpdHeadword).all()
    for i in headwords:
        if i.su is not None:
            print(i.lemma_1)


if __name__ == "__main__":
    main()
