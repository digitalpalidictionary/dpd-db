#!/usr/bin/env python3

import json

from bs4 import BeautifulSoup
from rich import print

from tools.sanskrit_translit import slp1_translit
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.pali_sort_key import sanskrit_sort_key
from tools.paths import ProjectPaths
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.tic_toc import tic, toc


# try another approach, if the key is the same, group
# them all together, dissolve the key and make one entry. 
# need to solve the slp translit issue
# fixup and simplify css
# or ... don't need to fix what isnt broken!

def main():
    tic()
    print("[bright_yellow]exporting Moneier Williams to GoldenDict, MDict & JSON")
    print("[green]preparing data")
    pth = ProjectPaths()
    
    mw_data_list = []

    mw_xml_path = "other_dictionaries/code/mw/source/mw_short.xml"

    with open(mw_xml_path) as f:
        soup = BeautifulSoup(f, "xml")

    headings_list = [
        "H1", "H1A", "H1B", "H1C", "H1E",
        "H2", "H2A", "H2B", "H2C", "H2E"
        "H3", "H3A", "H3B", "H3C", "H3E", 
        "H4", "H4A", "H4B", "H4C", "H4E"]
    
    css_path = "other_dictionaries/code/mw/mw.css"
    with open(css_path) as file:
        css = file.read()
    
    mw = soup.find(True)
    headings = mw.next_elements #type:ignore
    for i in headings:
        if i.name in headings_list:   #type:ignore

            slps = i.find_all("s1") #type:ignore
            for slp in slps:
                slp = slp1_translit(slp.text)

            headword = slp1_translit(i.key1.text) #type:ignore
            html = css
            html += str(i.body) #type:ignore

            if "ṃ" in headword:
                synonyms = add_niggahitas([headword], all=False)
                synonyms.remove(headword)
            else:
                synonyms = []
            
            mw_data_list.append({
                "word": headword,
                "definition_html": html,
                "definition_plain": "",
                "synonyms": synonyms
            })

    # sort into sanskrit alphabetical order
    mw_data_list = sorted(mw_data_list, key=lambda x: sanskrit_sort_key(x["word"]))

    # save as json
    print("[green]saving json")
    with open(pth.mw_json_path, "w") as file:
        json.dump(mw_data_list, file, indent=4, ensure_ascii=False)

    # save as goldendict
    print("[green]saving goldendict")

    bookname = "Monier-Williams' Sanskrit-English dictionary 1899"
    author = ""
    description = """<h3>Monier-Williams' Sanskrit-English dictionary 1899</h3><p>Etymologically and philologically arranged with special reference to cognate Indo-European languages, by Sir Monier Monier-Williams, M.A., K.C.I.E. Boden Professor of Sanskṛit, Hon. D.C.L. Oxon, Hon. L.L.D. Calcutta, Hon. Ph.D. Göttingen, Hon. fellow of University College and sometime fellow of Balliol College, Oxford.</p><p>New edition, greatly enlarged and improved with the collaboration of Professor E. Leumann, Ph.D. of the University of Strassburg, Professor C. Cappeller, Ph.D. of the University of Jena, and other scholars.</p><p>Published by Oxford at the the Clarendon Press, 1899.</p><p>For more Sanskrit dicitonaries please visit <a href="http://www.sanskrit-lexicon.uni-koeln.de">Cologne Sanskrit Lexicon</a> website.</p><p>Encoded by Bodhirasa 2024</p>"""
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
        mw_data_list, ifo, pth.mw_gd_path)

    # save as mdict
    print("[green]saving mdict")
    output_file = str(pth.mw_mdict_path)
    
    export_to_mdict(
        mw_data_list,
        output_file,
        bookname,
        f"{description}. {website}",
        h3_header=True
        )

    toc()

if __name__ == "__main__":
    main()