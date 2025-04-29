#!/usr/bin/env python3

"""
Search for missing or wrong phonetic changes according to TSV criteria.
"""

import pyperclip
import re

from rich import print
from rich.prompt import Prompt

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.db_search_string import db_search_string
from tools.meaning_construction import clean_construction
from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict
from tools.pali_sort_key import pali_list_sorter


def add_update_phonetic(db_session, db, csv):
	
	for c_counter, c in enumerate(csv):
		if c.initial == "-":
			break

		print("-"*40)
		for k, v in c.items():
			print(f"[green]{str(k):<15}: [white]{str(v)}")
		print()

		auto_updated = []
		auto_added = []
		manual_update = []

		for i_counter, i in enumerate(db):

			if (
				i.meaning_1 and
				i.construction and
				i.lemma_1 not in c.exceptions):

				# construction and base with:
				# no lines2, ph changes or root symbol
				construction_clean = clean_construction(i.construction)
				construction_clean = re.sub("√", "", construction_clean)
				construction_clean = re.sub("\\*", "", construction_clean)
				base_clean = clean_construction(i.root_base)
				base_clean = re.sub("√", "", base_clean)
				base_clean = re.sub("\\*", "", base_clean)

				# test construction
				if (
					(
						c.initial in construction_clean
	  					or c.initial in base_clean)
					and c.final in i.lemma_clean
					and c.correct not in i.phonetic
					and not (
						c.without in construction_clean
					 	or c.without in base_clean)
				):
					# auto update wrong to correct
					if (
						c.wrong
						and c.wrong in i.phonetic
					):
						i.phonetic = re.sub(
							f"\\b{c.wrong}\\b", str(c.correct), str(i.phonetic))
						auto_updated += [i.lemma_1]
					
					# if i.phonetic empty > auto add correct
					elif not i.phonetic:
						i.phonetic = c.correct
						auto_added += [i.lemma_1]
						
					# if i.phonetic not empty > compila a list to change manually
					else:
						manual_update += [i.lemma_1]

		
		print(f"[green]{'auto_updated':<15}: [white]{db_search_string(auto_updated)}")
		print(f"[green]{'auto_added':<15}: [white]{db_search_string(auto_added)}")
		
		manual_update_string = db_search_string(manual_update)
		print(f"[green]{'manual_update':<15}: [white]{manual_update_string}")
		pyperclip.copy(manual_update_string)

		if (
			(auto_updated or auto_added or manual_update) and
			c_counter < len(csv)-1
		):
			Prompt.ask("[yellow]Press any key to continue")

	# if auto_updated or auto_added:
	commitment = Prompt.ask("[yellow]Press 'c' to commit")
	if commitment == "c":
		db_session.commit()
		print("[red]Changes committed to db")
	else:
		print("[red]Changes not committed to db")

	db_session.close()



def finder(db, csv, string):
	found = []

	for i in db:
		for p in i.phonetic.split("\n"):
			if string == p:
				found += [i.lemma_1]
	
	if found:
		found_string = db_search_string(found)
		print(f"[cyan]{string}")
		print(f"[white]{found_string}")
		pyperclip.copy(found_string)
	else:
		print(None)


def list_all_phonetic_changes(db, csv):
	# all phonetic changes minus all csv.correct
	all_phonetic_set = set()
	correct = set()

	for c in csv:
		if (
			c.initial and
			c.initial != "-"
		):
			correct.update([c.correct])
	
	for i in db:
		if i.phonetic:
			phonetic = i.phonetic.split("\n")
			all_phonetic_set.update(phonetic)
	
	all_phonetic_set = all_phonetic_set.difference(correct)
	all_phonetic_list = pali_list_sorter(list(all_phonetic_set))
	
	# for p in all_phonetic_list:
	#     print(p)
	# print(len(all_phonetic_list))

	with open("temp/phonetic_changes.txt", "w") as f:
		for p in all_phonetic_list:
			f.write(f"{p}\n")
	


if __name__ == "__main__":
	pth = ProjectPaths()
	csv = read_tsv_dot_dict(pth.phonetic_changes_path)

	db_session = get_db_session(pth.dpd_db_path)
	db = db_session.query(DpdHeadword).all()

	list_all_phonetic_changes(db, csv)
	add_update_phonetic(db_session, db, csv)
	# finder(db, csv, "ṃs > s")

# FIXME test for xyz not in pali
# FIXME test for xyz not in base
# FIXME test for xyz not in construction
# FIXME exceptions must be a list
# FIXME without must be a list