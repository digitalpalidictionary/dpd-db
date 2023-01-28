import sqlite3
import re


class DpdDbTools:
	def __init__(self, db_file):
		self.conn = sqlite3.connect(db_file)
		self.c = self.conn.cursor()

	def fetch_pali(self):
		self.c.execute("""SELECT * FROM dpd LEFT JOIN roots ON dpd.root = roots.root""")
		self.fetchall = self.c.fetchall()
		return self.fetchall

	def fetch_roots(self):
		self.c.execute("""SELECT * FROM roots""")
		self.fetchall = self.c.fetchall()
		return self.fetchall

	def update_root_count(self):
		self.c.execute(
			"UPDATE roots SET root_counter = (SELECT COUNT(*) FROM dpd WHERE root = roots.root)")
		self.conn.commit()

	def close(self):
		self.conn.close()

	class PaliRow:
		def __init__(self, row):
			self.id = row[0]
			self.pali1 = row[1]
			self.pali2 = row[2]
			self.pos = row[3]
			self.grammar = row[4]
			self.derived_from = row[5]
			self.neg = row[6]
			self.verb = row[7]
			self.trans = row[8]
			self.plus_case = row[8]
			self.meaning1 = row[10]
			self.meaning_lit = row[11]
			self.non_ia = row[12]
			self.sanskrit = row[13]
			self.root = row[14]
			self.root_sign = row[15]
			self.base = row[16]
			self.family_root = row[17]
			self.family_word = row[18]
			self.family_compound = row[19]
			self.construction = row[20]
			self.derivative = row[21]
			self.suffix = row[22]
			self.phonetic = row[23]
			self.compound_type = row[24]
			self.compound_construction = row[25]
			self.non_root_in_comps = row[26]
			self.source1 = row[27]
			self.sutta1 = row[28]
			self.example1 = row[29]
			self.source2 = row[30]
			self.sutta2 = row[31]
			self.example2 = row[32]
			self.antonym = row[33]
			self.synonym = row[34]
			self.variant = row[35]
			self.commentary = row[36]
			self.notes = row[37]
			self.cognate = row[38]
			self.category = row[39]
			self.link = row[40]
			self.stem = row[41]
			self.pattern = row[42]
			self.meaning2 = row[43]
			self.root_counter = row[44]
			self.root = row[45]
			self.root_in_comps = row[46]
			self.root_has_verb = row[47]
			self.root_group = row[48]
			self.root_sign = row[49]
			self.root_base = row[50]
			self.root_meaning = row[51]
			self.sanskrit_root = row[52]
			self.sanskrit__root_meaning = row[53]
			self.sanskrit__root_class = row[54]
			self.root_example = row[55]
			self.dhatupatha_num = row[56]
			self.dhatupatha_root = row[57]
			self.dhatupatha_pali = row[58]
			self.dhatupatha_english = row[59]
			self.dhatumanjusa_num = row[60]
			self.dhatumanjusa_root = row[61]
			self.dhatumanjusa_pali = row[62]
			self.dhatumanjusa_english = row[63]
			self.dhatumala_root = row[64]
			self.dhatumala_pali = row[65]
			self.dhatumala_english = row[66]
			self.panini_root = row[67]
			self.panini_sanskrit = row[68]
			self.panini_english = row[69]
			self.note = row[70]
			self.matrix_test = row[71]


	class RootRow:
		def __init__(self, row):
			self.root_counter = row[0]
			self.root = row[1]
			self.root_clean = re.sub(" \\d.*$", "", self.root)
			self.root_in_comps = row[2]
			self.root_has_verb = row[3]
			self.root_group = row[4]
			self.root_sign = row[5]
			self.root_base = row[6]
			self.root_meaning = row[7]
			self.sanskrit_root = row[8]
			self.sanskrit__root_meaning = row[9]
			self.sanskrit__root_class = row[10]
			self.root_example = row[11]
			self.dhatupatha_num = row[12]
			self.dhatupatha_root = row[13]
			self.dhatupatha_pali = row[14]
			self.dhatupatha_english = row[15]
			self.dhatumanjusa_num = row[16]
			self.dhatumanjusa_root = row[17]
			self.dhatumanjusa_pali = row[18]
			self.dhatumanjusa_english = row[19]
			self.dhatumala_root = row[20]
			self.dhatumala_pali = row[21]
			self.dhatumala_english = row[22]
			self.panini_root = row[23]
			self.panini_sanskrit = row[24]
			self.panini_english = row[25]
			self.note = row[26]
			self.matrix_test = row[26]
	



if __name__ == "__main__":
	db = DpdDbTools("./dpd.db")
	dpd_db = db.fetch_pali()
	roots_db = db.fetch_roots()

	for row in dpd_db:
		p = db.PaliRow(row)
		print(f"{p.id} {p.pali1}")
	
	for row in roots_db:
		r = db.RootRow(row)
		if r.root_counter != 0:
			print(f"""{r.root_clean} {r.root_group} ({r.root_meaning})\n{r.sanskrit_root} {r.sanskrit__root_class} ({r.sanskrit__root_meaning})\n{r.dhatumala_root} {r.dhatumala_pali} {r.dhatumala_english}\n""")

	db.update_root_count()

	db.close()

