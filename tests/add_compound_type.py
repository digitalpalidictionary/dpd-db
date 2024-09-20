#!/usr/bin/env python3

"""
Search for missing or wrong compound types according to TSV criteria.
"""

import pyperclip
import re

from rich import print
from rich.prompt import Prompt

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.db_search_string import db_search_string
from tools.meaning_construction import make_meaning_combo
from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict


def main():
	pth = ProjectPaths()
	csv = read_tsv_dot_dict(pth.compound_type_path)

	db_session = get_db_session(pth.dpd_db_path)
	db = db_session.query(DpdHeadword).all()

	pos_exclusions = ["sandhi", "idiom", "aor"]
	
	for c_counter, c in enumerate(csv):
		print("-"*40)
		for k, v in c.items():
			print(f"[green]{str(k):<15}: [cyan]{str(v if v else '[red]None')}")
		print()
		if c.exceptions:
			exceptions = c.exceptions.split(", ")
		else:
			exceptions = []
		pos = c.pos.split(", ")
		type = c.type.split(", ")
		search_list: list = []
		i_counter = 0

		for i in db:
			if(
				not i.meaning_1 or
				i.lemma_1 in exceptions or 
				i.pos in pos_exclusions or
				", comp" not in i.grammar
			):
				continue
			if (
				c.pos != "any" and
				i.pos not in pos
			):
				continue

			if any(t in i.compound_type for t in type):
				continue

			if c.position == "first":
				pattern = f"^{c.word} "
			elif c.position == "middle":
				pattern = f" {c.word} "
			elif c.position == "last":
				pattern = f" {c.word}$"
			elif c.position == "any":
				pattern = f"\\b{c.word}\\b"
			else:
				print(f"[red]'{c.position}' position not recognised")
				break
			
			search_in = f"{i.construction}"
			if re.findall(pattern, search_in):
				search_list += [i.lemma_1]
				meaning = make_meaning_combo(i)
				i_counter += 1
				pyperclip.copy(i.lemma_1)
				printer(i, meaning)
				input()

		if search_list:
			print(i_counter)
			search_string = db_search_string(search_list)
			print(f"\n{search_string}")
			pyperclip.copy(search_string)
			if c_counter < len(csv)-1:
				user_input = Prompt.ask("[yellow]Press ENTER to continue or X to exit")
				if user_input == "x":
					break

def printer(i, meaning) -> None:
	string = ""
	string += f"[white]{i.lemma_1[:29]:<30}"
	string += f"[cyan]{i.pos:<10}"
	string += f"[white]{meaning[:49]:<50}"
	construction = re.sub("\n.+", "", i.construction)
	string += f"[cyan]{construction[:29]:<30}"
	string += f"[white]{i.compound_type[:14]:<15}"
	string += f"[cyan]{i.compound_construction[:19]:}"
	print(string)


if __name__ == "__main__":
	main()