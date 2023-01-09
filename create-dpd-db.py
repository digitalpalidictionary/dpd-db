import sqlite3
import pandas as pd

conn = sqlite3.connect('dpd.db')
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS dpd")
c.execute("DROP TABLE IF EXISTS roots")

# roots table

c.execute("""CREATE TABLE roots (
	"Fin" TEXT,
	"Count" INTEGER,
	"Root" TEXT PRIMARY KEY,
	"In Comps" TEXT,
	"V" TEXT,
	"Group" INTEGER,
	"Sign" TEXT,
	"Base" TEXT,
	"Meaning" TEXT,
	"Sk Root" TEXT,
	"Sk Root Mn" TEXT,
	"Cl" TEXT,
	"Example" TEXT,
	"Dhātupātha" INTEGER,
	"DpRoot" TEXT,
	"DpPāli" TEXT,
	"DpEnglish" TEXT,
	"Kaccāyana Dhātu Mañjūsā" INTEGER,
	"DmRoot" TEXT,
	"DmPāli" TEXT,
	"DmEnglish" TEXT,
	"Saddanītippakaraṇaṃ Dhātumālā" TEXT,
	"SnPāli" TEXT,
	"SnEnglish" TEXT,
	"Pāṇinīya Dhātupāṭha" TEXT,
	"PdSanskrit" TEXT,
	"PdEnglish" TEXT,
	"Note" TEXT,
	"Padaūpasiddhi" TEXT,
	"PrPāli" TEXT,
	"PrEnglish" TEXT,
	"blanks" INTEGER,
	"same/diff" TEXT,
	"matrix test"  TEXT
	)""")

roots = pd.read_csv("../csvs/roots.csv", sep="\t", dtype="str")
roots.fillna("", inplace=True)
roots.drop_duplicates(subset=["Root"], keep="first", inplace=True)
roots.to_sql('roots', conn, if_exists='append', index=False)

c.execute("""ALTER TABLE roots DROP COLUMN 'Fin'""")
c.execute("""ALTER TABLE roots RENAME COLUMN "Count" TO root_counter""")
c.execute("""ALTER TABLE roots RENAME COLUMN "Root" TO root""")
c.execute("""ALTER TABLE roots RENAME COLUMN "In Comps" TO root_in_comps""")
c.execute("""ALTER TABLE roots RENAME COLUMN "V" TO root_has_verb""")
c.execute("""ALTER TABLE roots RENAME COLUMN "Group" TO root_group""")
c.execute("""ALTER TABLE roots RENAME COLUMN "Sign" TO root_sign""")
c.execute("""ALTER TABLE roots RENAME COLUMN "Base" TO root_base""")
c.execute("""ALTER TABLE roots RENAME COLUMN "Meaning" TO root_meaning""")
c.execute("""ALTER TABLE roots RENAME COLUMN "Sk Root" TO sanskrit_root""")
c.execute("""ALTER TABLE roots RENAME COLUMN "Sk Root Mn" TO sanskrit_root_meaning""")
c.execute("""ALTER TABLE roots RENAME COLUMN "Cl" TO sanskrit_root_class""")
c.execute("""ALTER TABLE roots RENAME COLUMN "Example" TO root_example""")
c.execute("""ALTER TABLE roots RENAME COLUMN "Dhātupātha" TO dhatupatha_num""")
c.execute("""ALTER TABLE roots RENAME COLUMN "DpRoot" TO dhatupatha_root""")
c.execute("""ALTER TABLE roots RENAME COLUMN "DpPāli" TO dhatupatha_pali""")
c.execute("""ALTER TABLE roots RENAME COLUMN "DpEnglish" TO dhatupatha_english""")
c.execute("""ALTER TABLE roots RENAME COLUMN "Kaccāyana Dhātu Mañjūsā" TO dhatumanjusa_num""")
c.execute("""ALTER TABLE roots RENAME COLUMN "DmRoot" TO dhatumanjusa_root""")
c.execute("""ALTER TABLE roots RENAME COLUMN "DmPāli" TO dhatumanjusa_pali""")
c.execute("""ALTER TABLE roots RENAME COLUMN "DmEnglish" TO dhatumanjusa_english""")
c.execute("""ALTER TABLE roots RENAME COLUMN "Saddanītippakaraṇaṃ Dhātumālā" TO dhatumala_root""")
c.execute("""ALTER TABLE roots RENAME COLUMN "SnPāli" TO dhatumala_pali""")
c.execute("""ALTER TABLE roots RENAME COLUMN "SnEnglish" TO dhatumala_english""")
c.execute("""ALTER TABLE roots RENAME COLUMN "Pāṇinīya Dhātupāṭha" TO panini_root""")
c.execute("""ALTER TABLE roots RENAME COLUMN "PdSanskrit" TO panini_sanskrit""")
c.execute("""ALTER TABLE roots RENAME COLUMN "PdEnglish" TO panini_english""")
c.execute("""ALTER TABLE roots RENAME COLUMN "Note" TO note""")
c.execute("""ALTER TABLE roots DROP COLUMN 'Padaūpasiddhi'""")
c.execute("""ALTER TABLE roots DROP COLUMN 'PrPāli'""")
c.execute("""ALTER TABLE roots DROP COLUMN 'PrEnglish'""")
c.execute("""ALTER TABLE roots DROP COLUMN 'blanks'""")
c.execute("""ALTER TABLE roots DROP COLUMN 'same/diff'""")
c.execute("""ALTER TABLE roots RENAME COLUMN "matrix test" TO matrix_test""")


# dpd table

c.execute("""CREATE TABLE dpd (
	"ID" INTEGER PRIMARY KEY AUTOINCREMENT,
	"Pāli1" TEXT UNIQUE,
	"Pāli2" TEXT,
	"Fin" TEXT,
	"POS" TEXT,
	"Grammar" TEXT,
	"Derived from" TEXT,
	"Neg" TEXT,
	"Verb" TEXT,
	"Trans" TEXT,
	"Case" TEXT,
	"Meaning IN CONTEXT" TEXT,
	"Literal Meaning" TEXT,
	"Non IA" TEXT,
	"Sanskrit" TEXT,
	"Sk Root" TEXT,
	"Sk Root Mn" TEXT,
	"Cl" TEXT,
	"Pāli Root" TEXT,
	"Root In Comps" TEXT,
	"V" TEXT,
	"Grp" INTEGER,
	"Sgn" TEXT,
	"Root Meaning" TEXT,
	"Base" TEXT,
	"Family" TEXT,
	"Word Family" TEXT,
	"Family2" TEXT,
	"Construction" TEXT,
	"Derivative" TEXT,
	"Suffix" TEXT,
	"Phonetic Changes" TEXT,
	"Compound" TEXT,
	"Compound Construction" TEXT,
	"Non-Root In Comps" TEXT,
	"Source1" TEXT,
	"Sutta1" TEXT,
	"Example1" TEXT,
	"Source 2" TEXT,
	"Sutta2" TEXT,
	"Example 2" TEXT,
	"Antonyms" TEXT,
	"Synonyms – different word" TEXT,
	"Variant – same constr or diff reading" TEXT,
	"Commentary" TEXT,
	"Notes" TEXT,
	"Cognate" TEXT,
	"Category" TEXT,
	"Link" TEXT,
	"Stem" TEXT,
	"Pattern" TEXT,
	"Buddhadatta"  TEXT,
	FOREIGN KEY("Pāli Root") REFERENCES roots(root)
	)
	""")


dpd = pd.read_csv("../csvs/dpd-full.csv", sep="\t", dtype="str")
dpd.fillna("", inplace=True)
dpd.to_sql('dpd', conn, if_exists='append', index=True, index_label="ID")

c.execute("""ALTER TABLE dpd RENAME COLUMN "ID" TO id""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Pāli1" TO pali1""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Pāli2" TO pali2""")
c.execute("""ALTER TABLE dpd DROP COLUMN 'Fin'""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "POS" TO pos""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Grammar" TO grammar""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Derived from" TO derived_from""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Neg" TO neg""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Verb" TO verb""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Trans" TO trans""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Case" TO plus_case""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Meaning IN CONTEXT" TO meaning1""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Literal Meaning" TO meaning_lit""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Non IA" TO non_ia""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Sanskrit" TO sanskrit""")
c.execute("""ALTER TABLE dpd DROP COLUMN 'Sk Root'""")
c.execute("""ALTER TABLE dpd DROP COLUMN 'Sk Root Mn'""")
c.execute("""ALTER TABLE dpd DROP COLUMN 'Cl'""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Pāli Root" TO root""")
c.execute("""ALTER TABLE dpd DROP COLUMN 'Root In Comps'""")
c.execute("""ALTER TABLE dpd DROP COLUMN 'V'""")
c.execute("""ALTER TABLE dpd DROP COLUMN 'Grp'""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Sgn" TO root_sign""")
c.execute("""ALTER TABLE dpd DROP COLUMN 'Root Meaning'""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Base" TO base""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Family" TO family_root""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Word Family" TO family_word""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Family2" TO family_compound""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Construction" TO construction""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Derivative" TO derivative""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Suffix" TO suffix""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Phonetic Changes" TO phonetic""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Compound" TO compound_type""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Compound Construction" TO compound_construction""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Non-Root In Comps" TO non_root_in_comps""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Source1" TO source1""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Sutta1" TO sutta1""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Example1" TO example1""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Source 2" TO source2""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Sutta2" TO sutta2""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Example 2" TO example2""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Antonyms" TO antonym""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Synonyms – different word" TO synonym""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Variant – same constr or diff reading" TO variant""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Commentary" TO commentary""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Notes" TO notes""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Cognate" TO cognate""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Category" TO category""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Link" TO link""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Stem" TO stem""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Pattern" TO pattern""")
c.execute("""ALTER TABLE dpd RENAME COLUMN "Buddhadatta" TO meaning2 """)

conn.commit()
conn.close()

