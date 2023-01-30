#!/usr/bin/env python3

import re
from pathlib import Path
from dpd.models import PaliWord, PaliRoot
from dpd.db_helpers import create_db_if_not_exists, get_db_session

dpd_db_path = Path("dpd.sqlite3")
db_session = get_db_session(dpd_db_path)
dpd_db = db_session.query(PaliWord).all()

def anki_row(i, output_file):
	a1 = i.id
	a2 = i.pali_1
	a3 = i.pali_2

	if i.sutta_1 != None and i.sutta_2 != None:
		a4 = "√√"
	elif i.sutta_1 != None and i.sutta_2 == None:
		a4 = "√"
	else:
		a4= ""

	a5 = i.pos
	a6 = i.grammar
	a7 = i.derived_from
	a8 = i.neg
	a9 = i.verb
	a10 = i.trans
	a11 = i.plus_case
	a12 = i.meaning_1
	a13 = i.meaning_lit
	a14 = i.non_ia
	a15 = i.sanskrit

	if i.root != None:
		a16 = i.root.sanskrit_root
		a17 = i.root.sanskrit_root_meaning
		a18 = i.root.sanskrit_root_class

		a19 = re.sub(" \\d*$", "", i.root_key)
		a20 = i.root.root_in_comps
		a21 = i.root.root_has_verb
		a22 = i.root.root_group
		a23 = i.root_sign
		a24 = i.root.root_meaning
		a25 = i.root_base
	
	else:
		a16 = ""
		a17 = ""
		a18 = ""
		a19 = ""
		a20 = ""
		a21 = ""
		a22 = ""
		a23 = ""
		a24 = ""
		a25 = ""
	
	a26 = i.family_root
	a27 = i.family_word
	a28 = i.family_compound
	a29 = i.construction
	a30 = i.derivative
	a31 = i.suffix
	a32 = i.phonetic
	a33 = i.compound_type
	a34 = i.compound_construction
	a35 = i.non_root_in_comps
	a36 = i.source_1
	a37 = i.sutta_1
	a38 = i.example_1
	a39 = i.source_2
	a40 = i.sutta_2
	a41 = i.example_2
	a42 = i.antonym
	a43 = i.synonym
	a44 = i.variant
	a45 = i.commentary
	a46 = i.notes
	a47 = i.cognate
	a48 = i.category
	a49 = i.link
	a50 = i.stem
	a51 = i.pattern
	a52 = i.meaning_2

	row = (f"{a1}\t{a2}\t{a3}\t{a4}\t{a5}\t{a6}\t{a7}\t{a8}\t{a9}\t{a10}\t{a11}\t{a12}\t{a13}\t{a14}\t{a15}\t{a16}\t{a17}\t{a18}\t{a19}\t{a20}\t{a21}\t{a22}\t{a23}\t{a24}\t{a25}\t{a26}\t{a27}\t{a28}\t{a29}\t{a30}\t{a31}\t{a32}\t{a33}\t{a34}\t{a35}\t{a36}\t{a37}\t{a38}\t{a39}\t{a40}\t{a41}\t{a42}\t{a43}\t{a44}\t{a45}\t{a46}\t{a47}\t{a48}\t{a49}\t{a50}\t{a51}\t{a52}\n")
	row = remove_none(row)
	output_file.write(row)


def vocab():
	output_file = open("csvs4anki/vocab.csv", "w")
	for i in dpd_db:
		if i.meaning_1 != None and i.example_1 != None:
			anki_row(i, output_file)
	output_file.close()	


def commentary():
	output_file = open("csvs4anki/commentary.csv", "w")
	for i in dpd_db:
		if i.meaning_1 != None and i.example_1 == None:
			anki_row(i, output_file)
	output_file.close()


def pass1():
	output_file = open("csvs4anki/pass1.csv", "w")
	for i in dpd_db:
		if i.meaning1 == None:
			if i.category != None:
				if "pass1" in i.category:
					anki_row(i, output_file)
	output_file.close()


def remove_none(text):
	text = re.sub("None", "", text)
	return text

def main():
	vocab()
	commentary()
	pass1()

if __name__ == "__main__":
    main()
