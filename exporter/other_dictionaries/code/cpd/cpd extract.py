#!/usr/bin/env python3

import pandas as pd
import re


def clean_up():
	print("loading json")
	df = pd.read_json("en-critical.json", dtype="string")
	df.drop(labels=2, inplace=True, axis=1)
	df.rename({0: "pali", 1: "cpd"}, axis='columns', inplace=True)

	# replacements
	print("regex find and replace")
	df.replace("I", "l", inplace=True, regex=True)
	df.replace("<br\\/>", "", inplace=True, regex=True)
	df.replace("<span.+?>", "", inplace=True, regex=True)
	df.replace("<\\/span>", "", inplace=True, regex=True)
	df.replace("<sup>", "", inplace=True, regex=True)
	df.replace("<\\/sup>", "", inplace=True, regex=True)
	df.replace("<sub>", "", inplace=True, regex=True)
	df.replace("<\\/sub>", "", inplace=True, regex=True)
	df.replace('"$', "", inplace=True, regex=True)
	df.replace("rh", "ṃ", inplace=True, regex=True)
	df.replace("ç", "ś", inplace=True, regex=True)
	df.replace("ṁ", "ṃ", inplace=True, regex=True)
	df["pali"] = df["pali"].str.lower()

	# numbering system
	print("renumbering")
	for row in range(len(df)):
		headword = df.iloc[row, 0]
		meaning = df.iloc[row, 1]
		number = re.findall("^(\d|\d\d)", meaning)
		if number != []:
			df.iloc[row, 0] = f"{headword} {number[0]}"
			df.iloc[row, 1] = re.sub(f"^{number}", "", meaning)

	df.to_csv("output/cpd_cleaned.csv", sep="\t", index=None, quoting=1)


def make_df():
	print("making df")
	global df
	df = pd.read_csv("output/cpd_cleaned.csv", sep="\t")
	global df_length
	df_length = len(df)


def make_columns():
	print("making columns")

	# # ['Pāli1', 'Pāli2', 'Fin', 'POS', 'Grammar', 'Derived from', 'Neg', 'Verb', 'Trans', 'Case', 'Meaning IN CONTEXT', 'Literal Meaning', 'Non IA', 'Sanskrit', 'Sk Root', 'Sk Root Mn', 'Cl', 'Pāli Root', 'Root In Comps', 'V', 'Grp', 'Sgn', 'Root Meaning', 'Base', 'Family', 'Family2', 'Construction', 'Derivative', 'Suffix', 'Phonetic Changes', 'Compound', 'Compound Construction', 'Non-Root In Comps', 'Source1', 'Sutta1', 'Example1', 'Source 2', 'Sutta2', 'Example 2', 'Antonyms', 'Synonyms – different word', 'Variant – same constr or diff reading', 'Commentary', 'Notes', 'Cognate', 'Category', 'Link', 'Stem', 'Pattern', 'Buddhadatta', 'Date', 'test dupl', 'Data', 'Pāli3']

	df["pali2"] = ""
	df["fin"] = ""
	df["pos"] = ""
	df["grammar"] = ""
	df["derived"] = ""
	df["neg"] = ""
	df["verb"] = ""
	df["trans"] = ""
	df["case"] = ""
	df["meaning1"] = ""
	df["lit"] = ""
	df["nonia"] = ""
	df["sanskrit"] = ""
	df["skroot"] = ""
	df["skrootmn"] = ""
	df["skrootcl"] = ""
	df["root"] = ""
	df["rootincomps"] = ""
	df["rootv"] = ""
	df["rootgrp"] = ""
	df["rootsign"] = ""
	df["rootmn"] = ""
	df["base"] = ""
	df["family1"] = ""
	df["family2"] = ""
	df["construction"] = ""
	df["derivative"] = ""
	df["suffix"] = ""
	df["phonetic"] = ""
	df["compound"] = ""
	df["compoundconstr"] = ""
	df["nonrootincomp"] = ""
	df["source1"] = ""
	df["sutta1"] = ""
	df["exmaple1"] = ""
	df["source2"] = ""
	df["sutta2"] = ""
	df["exmaple2"] = ""
	df["antonym"] = ""
	df["synonyms"] = ""
	df["variant"] = ""
	df["commentary"] = ""
	df["notes"] = ""
	df["cognate"] = ""
	df["category"] = "cpd"
	df["link"] = ""
	df["stem"] = ""
	df["pattern"] = ""
	df["meaning"] = ""
	df["date"] = ""
	df["dupes"] = ""
	df["data"] = ""
	df["indpd"] = ""


def extract_pos():
	print("extracting pos")
	df["pos"] = df["cpd"].str.extract("(grd\\.|m\\. and n\\.|ind\\.|pp\\.|mfn|f\\.|f<\\/i>|m\\.|n\\.|aor\\.|m<\\/i>\\(<i>fn|m<\\/i>\\(<i>n\\?</i>|root|v\\.l\\.|w\\.r\\.|reading|ifc|v\\. l\\.|pr\\.|√|n<\\/b>|fut\\.|cond\\.|opt\\.|w\\. r\\. |<i>f<\\/i>|see<\\/i>|<i>see |v\\. r\\.|adv\\.|<i>read<\\/i><i>read |m<\\/i>.|abs\\.|pot\\.|<i>num\\.|indecl\\.)")

	df["pos"].replace("<\\/i>", "", inplace=True, regex=True)
	df["pos"].replace("<i>", "", inplace=True, regex=True)
	df["pos"].replace("(\.|,)", "", inplace=True, regex=True)
	df["pos"].replace("\\(", "", inplace=True, regex=True)
	df["pos"].replace("<\\/b>", "", inplace=True, regex=True)
	df["pos"].replace(" ", "", inplace=True, regex=True)
	
	df["pos"].replace("^m$", "masc", inplace=True, regex=True)
	df["pos"].replace("^f$", "fem", inplace=True, regex=True)
	df["pos"].replace("^n$", "nt", inplace=True, regex=True)
	df["pos"].replace("^mfn$", "adj", inplace=True, regex=True)
	df["pos"].replace("^√", "root", inplace=True, regex=True)
	df["pos"].replace("^vl$", "var", inplace=True, regex=True)
	df["pos"].replace("^reading$", "var", inplace=True, regex=True)
	df["pos"].replace("^read$", "var", inplace=True, regex=True)
	df["pos"].replace("^pot$", "opt", inplace=True, regex=True)
	df["pos"].replace("^indec$", "ind", inplace=True, regex=True)


def extract_grammar():
	print("extracting grammar")
	df["grammar"] = df["cpd"].str.findall("(grd\\.|abstr\\.)").str.join(", ")
	df["grammar"].replace("\\.", "", inplace=True, regex=True)
	df["grammar"].replace("grd", "ptp", inplace=True, regex=True)

def extract_neg():
	print("extracting neg")
	df["neg"] = df["cpd"].str.extract("<i>(neg\\.)")
	df["neg"].replace("<i>", "", inplace=True, regex=True)
	df["neg"].replace("\\.", "", inplace=True, regex=True)

def extract_verb():
	print("extracting verb")
	df["verb"] = df["cpd"].str.findall(
		"<i>(caus\\.|denom\\.|pass\\.|pass\\. caus\\.)").str.join(", ")
	df["verb"].replace("\\.", "", inplace=True, regex=True)

def extract_trans():
	print("extracting transitive")
	df["trans"] = df["cpd"].str.findall("<i>(trans\\.|intrans\\.)").str.join(", ")
	df["trans"].replace("\\.", "", inplace=True, regex=True)


def extract_case():
	print("extracting case")
	df["case"] = df["cpd"].str.findall("\swith (nom|acc|instr|dat|abl|gen|loc|voc)").str.join(",")


def extract_construction():
	print("extracting construction")
	df["construction"] = df["cpd"].str.extract("<b>(.+?)</b>")
	df["construction"].replace("\\[|\\]|\\(|\\)", "", inplace=True, regex=True)
	df["construction"].replace("-", " + ", inplace=True, regex=True)
	df["construction"] = df["construction"].str.lower()


def extract_derivative():
	print("extracting derivative")
	df["derivative"] = df["cpd"].str.extract("(scdry\\.)")
	df["derivative"].replace("scdry\\.", "taddhita", inplace=True, regex=True)


def extract_sanskrit():
	print("extracting sanskrit")
	df["sanskrit"] = df["cpd"].str.extract("sa.</i>(.+?)(\\)|\s)")[0]
	df["sanskrit"].replace(";|^ |,|\\]", "", inplace=True, regex=True)
	df["sanskrit"].replace("-", " + ", inplace=True, regex=True)
	# df["sanskrit"] = df["sanskrit"]


def extract_root():
	print("extracting root")
	df["root"] = df["cpd"].str.extract(
		"(√.+?)(,| |\\(|\\)|\\]|\d|;|\\/|\\<)")[0]
	df["root"].replace("<b>", "", inplace=True, regex=True)


def extract_antonym():
	print("extracting antonym")
	df["antonym"] = df["cpd"].str.extract("(opp. to<\\/i>.+?\s|opp.<\\/i>.+?\s)")
	df["antonym"].replace("opp. to<\\/i>", "", inplace=True, regex=True)
	df["antonym"].replace("opp.<\\/i>", "", inplace=True, regex=True)
	df["antonym"].replace("(, |;|\\(|\\)|;|-)", "", inplace=True, regex=True)
	df["antonym"].replace("(^ | $)", "", inplace=True, regex=True)


def extract_pattern():
	print("extracting pattern")
	df["pattern"] = df["cpd"].str.extract("\\((ikā)\\)")


def extract_meaning():
	print("extracting meaning")
	df["meaning"] = df["cpd"].str.findall("<i>(.*?;</i>|.*?</i>)").str.join("; ")
	df["meaning"].replace("(<i>|<\\/i>)", "", inplace=True, regex=True)
	df["meaning"].replace("^f; abstr\\. of; ", "", inplace=True, regex=True)
	df["meaning"].replace("^or; ", "", inplace=True, regex=True)
	df["meaning"].replace("^also; ", "", inplace=True, regex=True)
	df["meaning"].replace("^mfn\\.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^mfn\\. ", "", inplace=True, regex=True)
	df["meaning"].replace("^mfn\\., ", "", inplace=True, regex=True)
	df["meaning"].replace("^mf\\)n. ", "", inplace=True, regex=True)
	df["meaning"].replace("^f\\.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^f\\.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^f; ", "", inplace=True, regex=True)
	df["meaning"].replace("^f; ", "", inplace=True, regex=True)
	df["meaning"].replace("^f\\. ", "", inplace=True, regex=True)
	df["meaning"].replace("^m\\.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^m\\. ", "", inplace=True, regex=True)
	df["meaning"].replace("^m\\., ", "", inplace=True, regex=True)
	df["meaning"].replace("^n\\.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^n\\. ", "", inplace=True, regex=True)
	df["meaning"].replace("^n\\., ", "", inplace=True, regex=True)
	df["meaning"].replace("^ind\\.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^pr\\.; sg\\.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^pr\\. 3sg\\.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^pr\\. 3sg\\.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^pr\\. 3 sg\\.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^pr\\. 3 sg\\. ", "", inplace=True, regex=True)
	df["meaning"].replace("^pp\\. of prec; , ", "", inplace=True, regex=True)
	df["meaning"].replace("^pp\\. of; ", "", inplace=True, regex=True)
	df["meaning"].replace("^pp\\. of sa.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^\\(pp\\. of next\\), ", "", inplace=True, regex=True)
	df["meaning"].replace("^cf\\.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^cf; ", "", inplace=True, regex=True)
	df["meaning"].replace("^cf\\. ", "", inplace=True, regex=True)
	df["meaning"].replace("^sa.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^sa\\..+?; ", "", inplace=True, regex=True)
	df["meaning"].replace("^from sa\\.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^ts\\.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^or n\\., ", "", inplace=True, regex=True)
	df["meaning"].replace("^γ; ", "", inplace=True, regex=True)
	df["meaning"].replace("^q. v.; ", "", inplace=True, regex=True)
	df["meaning"].replace("^; ", "", inplace=True, regex=True)
	df["meaning"].replace("^ ", "", inplace=True, regex=True)
	df["meaning"].replace("\\[.+\\](,|, )", "", inplace=True, regex=True)


def save():
	print("saving")
	df.drop(labels="cpd", axis=1, inplace=True)
	df.to_csv("output/cpd_edited.csv", sep="\t", index=None, quoting=1)
	# df.to_excel("output/cpd_edited.xlsx", index=False)


def extractor():
	make_df()
	make_columns()
	extract_pos()
	extract_grammar()
	extract_neg()
	extract_verb()
	extract_trans()
	extract_case()
	extract_sanskrit()
	extract_root()
	extract_construction()
	extract_pattern()
	extract_antonym()
	extract_meaning()
	save()

clean_up()
extractor()

print("fin")