import re

from typing import Dict


def defintion_to_dict(
		file_name, ref_code, nikaya, book, title, subhead,
			bold, bold_end, commentary) -> Dict[str, str]:
		dict = {
			"file_name" : file_name,
			"ref_code" : ref_code,
			"nikaya" : nikaya,
			"book" : book,
			"title" : title,
			"subhead" : subhead,
			"bold" : bold,
			"bold_end" : bold_end,
			"commentary" : commentary}
		return dict


file_list = {

	# vinaya mula
	"vin01m.mul.xml":"VIN",
    "vin02m1.mul.xml": "VIN",
    "vin02m2.mul.xml": "VIN",
    "vin02m3.mul.xml": "VIN",
    "vin02m4.mul.xml": "VIN",

	# kn mula
	"s0515m.mul.xml": "NIDD1",
	"s0516m.mul.xml": "NIDD2",
	"s0517m.mul.xml": "PM",
	"s0519m.mul.xml": "NP",
	"s0520m.nrf.xml": "PTP",
	
	# abhidhamma mula
    "abh01m.mul.xml": "DHS",

	# vinaya commentary
	"vin01a.att.xml": "VINa",
	"vin02a1.att.xml": "VINa",
	"vin02a2.att.xml": "VINa",
	"vin02a3.att.xml": "VINa",
	"vin02a4.att.xml": "VINa",

	# sutta commentary
	"s0101a.att.xml": "DNa",
	"s0102a.att.xml": "DNa",
	"s0103a.att.xml": "DNa",

	"s0201a.att.xml": "MNa",
	"s0202a.att.xml": "MNa",
	"s0203a.att.xml": "MNa",

	"s0301a.att.xml" : "SNa",
	"s0302a.att.xml": "SNa",
	"s0303a.att.xml": "SNa",
	"s0304a.att.xml": "SNa",
	"s0305a.att.xml": "SNa",

	"s0401a.att.xml": "ANa",
	"s0402a.att.xml": "ANa",
	"s0403a.att.xml": "ANa",
	"s0404a.att.xml": "ANa",

	"s0501a.att.xml": "KPa",
	"s0502a.att.xml": "DHPa",
	"s0503a.att.xml": "UDa",
	"s0504a.att.xml": "ITIa",
	"s0505a.att.xml": "SNPa",
	"s0506a.att.xml": "VVa",
	"s0507a.att.xml": "PVa",
	"s0508a1.att.xml": "THa",
	"s0508a2.att.xml": "THa",
	"s0509a.att.xml": "THIa",
	"s0510a.att.xml": "APAa",
	"s0511a.att.xml": "BVa",
	"s0512a.att.xml": "CPa",
	"s0513a1.att.xml": "JAa",
	"s0513a2.att.xml": "JAa",
	"s0513a3.att.xml": "JAa",
	"s0513a4.att.xml": "JAa",
	"s0514a1.att.xml": "JAa",
	"s0514a2.att.xml": "JAa",
	"s0514a3.att.xml": "JAa",
	"s0515a.att.xml": "NIDD1a",
	"s0516a.att.xml": "NIDD2a",
	"s0517a.att.xml": "PMa",
	"s0519a.att.xml": "NPa",
	"s0501t.nrf.xml" : "NPt",

	# abhidhamma commentary
   	"abh01a.att.xml" : "ADHa",
    "abh02a.att.xml" : "ADHa",
    "abh03a.att.xml" : "ADHa",
	
	# visuddhimagga
    "e0101n.mul.xml": "VISM",
    "e0102n.mul.xml": "VISM",

	# vinaya sub-commentaries
	"vin01t1.tik.xml": "VINt",
    "vin01t2.tik.xml": "VINt",
    "vin02t.tik.xml": "VINt",
    "vin04t.nrf.xml": "KVa",
    "vin05t.nrf.xml": "VSa",
    "vin06t.nrf.xml": "VBt",
    "vin07t.nrf.xml": "VMVt",
    "vin08t.nrf.xml": "VAt",
    "vin09t.nrf.xml": "KVt",
    "vin10t.nrf.xml": "VVUt",
    "vin11t.nrf.xml": "VVt",
    "vin12t.nrf.xml": "PYt",
    "vin13t.nrf.xml": "VINt",

	# sutta sub-commentaries
    "s0101t.tik.xml": "DNt",
    "s0102t.tik.xml": "DNt",
    "s0103t.tik.xml": "DNt",
	"s0104t.nrf.xml": "DNt",
	"s0105t.nrf.xml": "DNt",

    "s0201t.tik.xml": "MNt",
    "s0202t.tik.xml": "MNt",
    "s0203t.tik.xml": "MNt",

    "s0301t.tik.xml": "SNt",
    "s0302t.tik.xml": "SNt",
    "s0303t.tik.xml": "SNt",
    "s0304t.tik.xml": "SNt",
    "s0305t.tik.xml": "SNt",

    "s0401t.tik.xml": "ANt",
    "s0402t.tik.xml": "ANt",
    "s0403t.tik.xml": "ANt",
    "s0404t.tik.xml": "ANt",

    "s0519t.tik.xml": "NPt",

	# abhidhamma sub-commentary
	"abh01t.tik.xml": "DHSt",
    "abh02t.tik.xml": "VIBHt",
    "abh03t.tik.xml": "ADHt",
	"abh04t.nrf.xml": "DHSt",
    "abh05t.nrf.xml": "ADHt",
    "abh06t.nrf.xml": "ADHt",
    "abh07t.nrf.xml": "ADHt",
    "abh08t.nrf.xml": "ADHt",
    "abh09t.nrf.xml": "ADHt",

	# visuddhimagga commentary
   	"e0103n.att.xml": "VISMa",
	"e0104n.att.xml": "VISMa",

    # abhidhānappadīpikā
	"e0809n.nrf.xml": "APP",
	"e0810n.nrf.xml": "APt",
}

def dissolve_empty_siblings(para, bolds):
	"""remove empty elements"""
	
	# unwrap bolds with one spaces inbetween
	for bold in bolds:
		try:
			if (
				bold.next_sibling == ' ' and 
				bold.next_sibling.next_sibling.attrs == {'rend': 'bold'} # type:ignore
			):
				appended_text = bold.next_sibling.next_sibling.text # type:ignore
				bold.append(f" {appended_text}")
				bold.next_sibling.next_sibling.decompose() # type:ignore
		except AttributeError:
			pass
	
	# unwrap bolds with two spaces inbetween
	for bold in bolds:
		try:
			if (
				bold.next_sibling == ' ' and
				bold.next_sibling.next_sibling == ' ' and # type:ignore
				bold.next_sibling.next_sibling.next_sibling.attrs == {'rend': 'bold'} # type:ignore
			):
				appended_text = bold.next_sibling.next_sibling.next_sibling.text # type:ignore
				bold.append(f" {appended_text}")
				bold.next_sibling.next_sibling.next_sibling.decompose() # type:ignore
		except AttributeError:
			pass

	# unwrap bolds with three spaces inbetween
	for bold in bolds:
		try:
			if (
				bold.next_sibling == ' ' and
				bold.next_sibling.next_sibling == ' ' and	# type:ignore
				bold.next_sibling.next_sibling.next_sibling == ' ' and	# type:ignore
				bold.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling == ' 'and	# type:ignore
				bold.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.attrs == {'rend': 'bold'}	# type:ignore
			):
				appended_text = bold.next_sibling.next_sibling.next_sibling.next_sibling.text	# type:ignore
				bold.append(f" {appended_text}")
				bold.next_sibling.next_sibling.next_sibling.next_sibling.decompose() # type:ignore
		except AttributeError:
			pass
	
	# unwrap empty bold strings
	for bold in bolds:
		if bold.text == " ":
			bold.unwrap()
	
		if (
			bold.text == ""
			and bold.attrs == {"rend": "bold"}
			and bold.next_sibling
		):
			bold.replace_with(" ")
	
		if "vimānavatthuṃ" in bold.text:
				pass
	
	return bolds

	
def get_nikaya_headings_div(file_name, div, para, subhead):
	"""get headings for nikaya texts"""

	if file_name == "s0515m.mul.xml":
		title = "1. aṭṭhakavaggo"
		if div["type"] == "book":
			title = div.p.string
		if div.head["rend"] == "chapter":
			subhead = div.head.string

	else:
		try:
			title = div.head.string
		except:
			title = div.p.string
		title = re.sub("^\\(\\d*\\) ", "", title)

		if "subhead" in str(para):
			subhead = para.string
		elif "subsubhead" in str(para):
			subhead = para.string
		elif "chapter" in str(para):
			subhead = para.string

	return title, subhead


def get_headings_no_div(para, file_name, nikaya, book, title, subhead):
	"""get headings for nikaya texts""" 
	if para["rend"] == "nikaya":
		nikaya = para.string
	if para["rend"] == "book":
		book = para.string
	if para["rend"] == "title":
		title = para.string
	if para["rend"] == "chapter":
		title = para.string
	if para["rend"] == "subhead":
		subhead = para.string
	if para["rend"] == "subsubhead":
		subhead = para.string
	if re.findall("\\[\\d*\\]", str(para)):
		subhead = para.string
		subhead = re.sub("^ *", "", str(subhead))
	
	jaa = ["s0513a2.att.xml", "s0513a3.att.xml"]
	if file_name in jaa:
		nikaya = "khuddakanikāye"
	
	if file_name == "s0514a1.att.xml":
		nikaya = "khuddakanikāye"
		book = "jātaka-aṭṭhakathā"
		title = "(chaṭṭho bhāgo)"

	if file_name == "s0515a.att.xml":
		title = "1. aṭṭhakavaggo"
		if para["rend"] == "chapter":
			subhead = para.string

	if file_name == "s0519a.att.xml":
		nikaya = "khuddakanikāye"
		if para["rend"] == "nikaya": # some subheads tagged nikaya
			subhead = para.string
	
	if file_name == "vin10t.nrf.xml":
		book = "vinayavinicchayo uttaravinicchayo"
	
	if file_name == "abh03a.att.xml":
		if para["rend"] == "chapter":
			book = para.string

	if file_name == "abh05t.nrf.xml":
		book = "pañcapakaraṇa-anuṭīkā"
	
	if file_name == "e0810n.nrf.xml":
		if para["rend"] == "subsubhead":
			title = para.string

	aññā = ["e0101n.mul.xml", "e0102n.mul.xml", "e0103n.att.xml", "e0104n.att.xml", "e0809n.nrf.xml", "e0810n.nrf.xml"]
	if file_name in aññā:
		nikaya = "aññā"
	
	vin_t = ["vin04t.nrf.xml", "vin08t.nrf.xml", "vin09t.nrf.xml", "vin10t.nrf.xml", "vin11t.nrf.xml", "vin13t.nrf.xml"]
	if file_name in vin_t:
		nikaya = "vinayapiṭake"

	abh_t = ["abh06t.nrf.xml", "abh07t.nrf.xml", "abh08t.nrf.xml", "abh09t.nrf.xml"]
	if file_name in abh_t:
		nikaya = "abhidhammapiṭake"
		if para["rend"] == "nikaya":
			book = para.string

	return nikaya, book, title, subhead

useless_beginnings = ["   ", "  ", " ", "\\.", "\\. ", "\\. ", " \\.", " \\. ", ",", " ,", " , "]
useless_beginnings_str = "|".join(useless_beginnings)
useless_endings = ["  ti.", " ti.", "ti.", "'ti.", "nti.", "'nti.", "' nti.", "."]


def text_cleaner(text):
	text = re.sub(" – ‘‘", ", ", text)
	text = re.sub("^‘‘", "", text)
	text = re.sub("’’", "'", text)
	text = re.sub("‘", "", text)
	text = re.sub("’", "'", text)
	text = re.sub("‘‘", "'", text)
	text = re.sub("‘‘", "", text)
	text = re.sub(" ’", "", text)
	text = re.sub("'", "'", text)
	text = re.sub("'nti", "n'ti", text)
	text = re.sub("…pe॰…", " …", text)
	text = re.sub(" – ", ", ", text)
	text = re.sub(" \\.", ".", text)
	text = re.sub(" ,", ",", text)
	text = re.sub(";", ",", text)
	text = re.sub("'\\.", ".", text)
	text = re.sub("\\॰", ".", text)
	text = re.sub("  ", " ", text)
	return text.lower()


def get_bold_strings(bold):
	"""get bold strings previous next and cleanup"""

	# bold_p are the previous sentences which may contain 
	# relavant information, especially in ṭīkā
	# should start clean after a . or ; or )

	def simplify_bold_tag(text):
		# simplify the tag
		text = re.sub("""\\<hi rend\\="bold">""", "<b>", text)
		# simplify the tag end
		text = re.sub("""<\\/hi>""", "</b>", text)
		return text
	
	bold_text = f"{bold}"
	bold_text = text_cleaner(bold_text)
	bold_text = simplify_bold_tag(bold_text)
	bold_clean = bold_text.replace("<b>", "").replace("</b>", "")

	bold_p = ""

	prev_sibs = bold.previous_siblings
	for prev_sib in prev_sibs:
			try:
				bold_p = f"{prev_sib}{bold_p}"
			except:
				pass
	
	bold_p = text_cleaner(bold_p)
	bold_p = simplify_bold_tag(bold_p)
	
	# remove numbers at the beginning
	bold_p = re.sub("^\\d+\\.d+\\.", "", bold_p)
	bold_p = re.sub("^\\d+\\.", "", bold_p)
	bold_p = re.sub("^\\d+ ", "", bold_p)
	bold_p = re.sub("^\\d+", "", bold_p)

	# remove useless_beginnings
	bold_p = re.sub(f"^({useless_beginnings_str})", "", bold_p)
	bold_p = re.sub("^ $", "", bold_p)

	non_letters = re.compile(" |,|\\.|;")
	if re.match(non_letters, bold_text):
		bold_text = bold_text[1:]
		bold_p = f"{bold_p} "

	# bold next sentence = bold_n
	bold_n = ""

	next_sibs = bold.next_siblings
	for next_sib in next_sibs:
		try:
			bold_n = f"{bold_n}{next_sib}"
		except:
			pass
	
	bold_n = text_cleaner(bold_n)
	bold_n = simplify_bold_tag(bold_n)

	# remove space before ti
	bold_n = re.sub(" *(ti)( |\\.)", "\\1\\2", bold_n)

	# remove useless
	bold_n = re.sub(f"^({useless_beginnings})$", "", bold_n)
	bold_n = bold_n.replace("[iti bhagavā]", "")

	# bold end
	bold_e = str(bold_n)

	# remove trailing sentences
	bold_e = re.sub(" .+$", "", str(bold_e))
	bold_e = bold_e.replace("[iti bhagavā]", "")
	bold_e = text_cleaner(bold_e)

	bold_comp = f"{bold_p}{bold_text}{bold_n}"

	return bold_clean, bold_e, bold_comp, bold_n

