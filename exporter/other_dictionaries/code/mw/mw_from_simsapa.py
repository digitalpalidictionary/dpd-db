"""Extract MW from Simsapa.
Export to GoldenDict andMDict.
"""

import sqlite3

from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.mdict_exporter import export_to_mdict

from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.printer import p_title, p_green, p_yes


class GlobalVars():
    pth: ProjectPaths = ProjectPaths()
    mw_data: list[tuple[str, str, str]]
    dict_data: list[DictEntry] = []


def extract_mw_from_simsapa(g: GlobalVars):
    """Query Simsapa DB for MW data."""
    p_green("querying simsapa db")

    simsapa_db_path = "../../.local/share/simsapa/assets/appdata.sqlite3"
    conn = sqlite3.connect(simsapa_db_path)
    c = conn.cursor()
    c.execute("""SELECT word, definition_html, synonyms FROM dict_words WHERE source_uid is 'mw'""")
    g.mw_data = c.fetchall()
    p_yes(len(g.mw_data))


def make_dict_data(g: GlobalVars):
    p_green("making data list")

    for i in g.mw_data:
        headword, html, synonyms = i
        headword = headword.replace("ṁ", "ṃ")
        html = html.replace("ṁ", "ṃ")

        if "ṃ" in headword:
            synonyms = add_niggahitas([headword])
        else:
            synonyms = []

        dict_entry = DictEntry(
            word = headword,
            definition_html = html,
            definition_plain = "",
            synonyms = synonyms
        )
        g.dict_data.append(dict_entry)
    p_yes(len(g.dict_data))


def save_goldendict_and_mdict(g: GlobalVars):

    dict_info = DictInfo(
        bookname = "Monier Williams Sanskrit English Dictionary 1899",
        author = "Sir Monier Monier Williams",
        description = """<h3>Monier-Williams' Sanskrit-English dictionary 1899</h3><p>Etymologically and philologically arranged with special reference to cognate Indo-European languages, by Sir Monier Monier-Williams, M.A., K.C.I.E. Boden Professor of Sanskṛit, Hon. D.C.L. Oxon, Hon. L.L.D. Calcutta, Hon. Ph.D. Göttingen, Hon. fellow of University College and sometime fellow of Balliol College, Oxford.</p><p>New edition, greatly enlarged and improved with the collaboration of Professor E. Leumann, Ph.D. of the University of Strassburg, Professor C. Cappeller, Ph.D. of the University of Jena, and other scholars.</p><p>Published by Oxford at the the Clarendon Press, 1899.</p><p>For more Sanskrit dicitonaries please visit <a href="http://www.sanskrit-lexicon.uni-koeln.de">Cologne Sanskrit Lexicon</a> website.</p><p>Encoded by Bodhirasa 2024</p>""",
        website = "https://www.sanskrit-lexicon.uni-koeln.de",
        source_lang = "sa",
        target_lang = "en",
    )
    
    dict_vars = DictVariables(
        css_path = None,
        js_paths = None,
        gd_path = g.pth.mw_gd_path,
        md_path = g.pth.mw_mdict_path,
        dict_name= "mw",
        icon_path = None,
        zip_up = True,
        delete_original = True
    )

    # save goldendict
    export_to_goldendict_with_pyglossary(
        dict_info, 
        dict_vars,
        g.dict_data,
    )

    # save as mdict
    export_to_mdict(
        dict_info, 
        dict_vars,
        g.dict_data
    )


def main():
    tic()
    p_title("exporting mw to GoldenDict, MDict")
    g = GlobalVars()
    extract_mw_from_simsapa(g)
    make_dict_data(g)
    save_goldendict_and_mdict(g)
    toc()


if __name__ == "__main__":
    main()

