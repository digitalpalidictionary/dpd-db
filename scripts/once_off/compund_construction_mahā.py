#!/usr/bin/env python3

"""
Search for mahanta in compound construction and replace with mahā.
"""

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord

from tools.paths import ProjectPaths


def main():
	pth = ProjectPaths()

	db_session = get_db_session(pth.dpd_db_path)
	db = db_session.query(PaliWord).all()
	
	for i in db:
		if (
			"mahanta" in str(i.compound_construction) and
			"mahā" in str(i.construction)
		):
			i.compound_construction = i.compound_construction.replace("mahanta", "mahā")
			print(f"{i.pali_1:<30}{i.compound_construction}")

	db_session.commit()
        


if __name__ == "__main__":
	main()