import sqlite3


class DpdDbTools:
	def __init__(self, location):
		self.conn = sqlite3.connect(location)
		self.c = self.conn.cursor()

	def fetch_all(self):
		self.c.execute("""SELECT * FROM dpd LEFT JOIN roots ON dpd.root = roots.root""")
		self.fetchall = self.c.fetchall()
		return self.fetchall

	class RowData:
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

db_location = "./dpd.db"
db = DpdDbTools(db_location)
fetchall = db.fetch_all()

for data_row in fetchall:
	w = db.RowData(data_row)
	print(f"{w.id} {w.pali1}")
