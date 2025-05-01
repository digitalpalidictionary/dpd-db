#!/usr/bin/env python3

"""Search bold_definitions using vanilla find or regex."""

import re
from typing import List

from rich import print

from db.db_helpers import get_db_session
from db.models import BoldDefinition
from tools.paths import ProjectPaths


class BoldDefinitionsSearchManager:
    def __init__(self):
        self.pth = ProjectPaths()
        self.session = get_db_session(self.pth.dpd_db_path)

    def search(
        self, search1: str, search2: str, option: str = "regex"
    ) -> List[BoldDefinition]:
        """Main search method with options matching db_search_bd"""
        if not search1 and not search2:
            return []

        if option == "starts_with":
            search1 = f"^{search1}"
            return (
                self.session.query(BoldDefinition)
                .filter(BoldDefinition.bold.regexp_match(search1))
                .filter(BoldDefinition.commentary.regexp_match(search2))
                .all()
            )
        elif option == "regex":
            return (
                self.session.query(BoldDefinition)
                .filter(BoldDefinition.bold.regexp_match(search1))
                .filter(BoldDefinition.commentary.regexp_match(search2))
                .all()
            )
        elif option == "fuzzy":
            from exporter.webapp.toolkit import fuzzy_replace

            search1 = fuzzy_replace(search1)
            search2 = fuzzy_replace(search2)
            return (
                self.session.query(BoldDefinition)
                .filter(BoldDefinition.bold.regexp_match(search1))
                .filter(BoldDefinition.commentary.regexp_match(search2))
                .all()
            )
        else:  # plain search
            return (
                self.session.query(BoldDefinition)
                .filter(BoldDefinition.bold.ilike(f"%{search1}%"))
                .filter(BoldDefinition.commentary.ilike(f"%{search2}%"))
                .all()
            )


if __name__ == "__main__":
    searcher = BoldDefinitionsSearchManager()
    search1 = input("enter search1: ")
    search2 = input("enter search2: ")
    search_results = searcher.search(search1, search2)
    print(f"{len(search_results)} results found")
