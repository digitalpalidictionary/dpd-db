#!/usr/bin/env python3

"""Search bold_definitions using vanilla find or regex."""

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
        self,
        search1: str,
        search2: str,
        option: str = "regex",
        limit: int | None = None,
    ) -> List[BoldDefinition]:
        """Main search method with options matching db_search_bd.

        Pass ``limit`` to cap the number of rows returned (e.g. for a GUI that
        cannot render an unbounded result set). Default ``None`` returns all rows.
        """
        if not search1 and not search2:
            return []

        query = self.session.query(BoldDefinition)

        if option == "starts_with":
            query = query.filter(
                BoldDefinition.bold.regexp_match(f"^{search1}")
            ).filter(BoldDefinition.commentary.regexp_match(search2))
        elif option == "regex":
            query = query.filter(BoldDefinition.bold.regexp_match(search1)).filter(
                BoldDefinition.commentary.regexp_match(search2)
            )
        elif option == "fuzzy":
            from exporter.webapp.toolkit import fuzzy_replace

            query = query.filter(
                BoldDefinition.bold.regexp_match(fuzzy_replace(search1))
            ).filter(BoldDefinition.commentary.regexp_match(fuzzy_replace(search2)))
        else:  # plain search
            query = query.filter(BoldDefinition.bold.ilike(f"%{search1}%")).filter(
                BoldDefinition.commentary.ilike(f"%{search2}%")
            )

        if limit is not None:
            query = query.limit(limit)

        return query.all()


if __name__ == "__main__":
    searcher = BoldDefinitionsSearchManager()
    search1 = input("enter search1: ")
    search2 = input("enter search2: ")
    search_results = searcher.search(search1, search2)
    print(f"{len(search_results)} results found")
