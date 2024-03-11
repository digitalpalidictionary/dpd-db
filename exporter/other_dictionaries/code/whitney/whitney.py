#!/usr/bin/env python3
# coding: utf-8

import json
import os
import re

from bs4 import BeautifulSoup
from rich import print

from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.pali_sort_key import sanskrit_sort_key
from tools.paths import ProjectPaths
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.tic_toc import tic, toc


def main():
	tic()
	print("[bright_yellow]exporting whitney to gd, mdict & json")
	print("[green]preparing data")
	pth = ProjectPaths()

	with open(pth.whitney_css_dir, "r") as c:
		css = c.read()

	whitney_data_list = []
	for filename in os.listdir(pth.whitney_source_dir):

		with open(f"{pth.whitney_source_dir}/{filename}") as f:
			soup = BeautifulSoup(f, "xml")
			root = str(soup.h2)
			if re.findall("√", root):
				html = css
				html += str(soup.h2)
				root = re.sub("<h2>(.+?)(<| |\\().+", "\\1", str(root))
				root = root.replace("ṁ", "ṃ")
				root_clean = re.sub("√", "", root)
				root_clean = re.sub("\\d", "", root_clean)
				try:
					for child in soup.h2.next_siblings:
						if "<a" in str(child):
							child = str(child)
							child = re.sub("""<a href.+?">""", "", child)
							child = re.sub("""</a>""", "", child)
							child = re.sub("""<b>""", "<b>√", child)
							html += child
						else:
							html += str(child)
				except Exception:
					print(f"{filename} has no <h2> ")
				html += "</body></html>"
				
				# fixes
				html = html.replace("<i>", "<whi>")
				html = html.replace("</i>", "</whi>")
				html = html.replace("<b>", "<whb>")
				html = html.replace("</b>", "</whb>")
				html = html.replace("ç", "ś")
				html = html.replace("Ç", "Ś")

				synonyms = [root_clean]
				if "ṅ" in root:
					synonyms += [root.replace("ṅ", "ṃ")]
					synonyms += [root_clean.replace("ṅ", "ṃ")]
				synonyms = add_niggahitas(synonyms)

				whitney_data_list.append({
					"word": root,
					"definition_html": html,
	  				"definition_plain": "",
					"synonyms": synonyms
				})

    # sort into sanskrit alphabetical order
	whitney_data_list = sorted(whitney_data_list, key=lambda x: sanskrit_sort_key(x["word"]))

    # save as json
	print("[green]saving json")
	with open(pth.whitney_json_path, "w") as file:
		json.dump(whitney_data_list, file, indent=4, ensure_ascii=False)


    # save as goldendict
	print("[green]saving goldendict")

	bookname = "Whitney Sanskrit Roots"
	author = "William Dwight Whitney"
	description = """<h3>The Roots, Verb-Forms and Primary Derivatives of the Sanskrit Language by William Dwight Whitney</h3><p>Published by Trübner & Co, London, 1895.</p><p>Availble as part of the <a href='https://www.sanskrit-lexicon.uni-koeln.de/scans/csl-whitroot/disp/index.php'>Cologne Sanskrit Lexicon</a></p><p>Encoded by Bodhirasa 2024.</p>"""
	website = "www.sanskrit-lexicon.uni-koeln.de"

	ifo = ifo_from_opts(
		{
			"bookname": bookname,
			"author": author,
			"description": description,
			"website": website,
		}
	)

	export_words_as_stardict_zip(
		whitney_data_list, ifo, pth.whitney_gd_path)

    # save as mdict
	print("[green]saving mdict")
	output_file = str(pth.whitney_mdict_path)
	
	export_to_mdict(
		whitney_data_list,
		output_file,
		bookname,
		description,
		h3_header=False)

	toc()

if __name__ == "__main__":
	main()