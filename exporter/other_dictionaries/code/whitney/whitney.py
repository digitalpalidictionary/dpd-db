#!/usr/bin/env python3
# coding: utf-8

import os
import re

from bs4 import BeautifulSoup
from rich import print

from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc


def main():
	tic()
	print("[bright_yellow]exporting Whitney to GoldenDict and MDict")
	print("[green]preparing data")
	pth = ProjectPaths()

	dict_data: list[DictEntry] = []

	with open(pth.whitney_css_path, "r") as c:
		css = c.read()

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
			
				dict_entry = DictEntry(
					word = root,
					definition_html = html,
					definition_plain = "",
					synonyms = synonyms)
				dict_data.append(dict_entry)

    # save as goldendict
	print("[green]saving goldendict")

	dict_info = DictInfo(
        bookname = "Whitney Sanskrit Roots",
        author = "William Dwight Whitney",
        description = """<h3>The Roots, Verb-Forms and Primary Derivatives of the Sanskrit Language by William Dwight Whitney</h3><p>Published by Trübner & Co, London, 1895.</p><p>Availble as part of the <a href='https://www.sanskrit-lexicon.uni-koeln.de/scans/csl-whitroot/disp/index.php'>Cologne Sanskrit Lexicon</a></p><p>Encoded by Bodhirasa 2024.</p>""",
        website = "www.sanskrit-lexicon.uni-koeln.de",
        source_lang = "sa",
        target_lang = "en",
    )
	
	dict_vars = DictVariables(
        css_path = pth.whitney_css_path,
        js_paths = None,
        gd_path = pth.whitney_gd_path,
        md_path = pth.whitney_mdict_path,
        dict_name= "whitney",
        icon_path = None,
        zip_up=True,
        delete_original=True
    )
	
	export_to_goldendict_with_pyglossary(
        dict_info, 
        dict_vars,
        dict_data, 
        zip_synonyms=False
    )

    # save as mdict
	print("[green]saving mdict")
	
	export_to_mdict(
        dict_info, 
        dict_vars,
        dict_data
	)

	toc()

if __name__ == "__main__":
	main()