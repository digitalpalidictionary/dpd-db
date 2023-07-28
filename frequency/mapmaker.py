#!/usr/bin/env python3

"""Create frequency map data and HTML and save into database."""

import pandas as pd
import pickle
import re

from rich import print
from mako.template import Template
from sqlalchemy import update

from db.get_db_session import get_db_session
from db.models import PaliWord, DerivedData

from tools.configger import config_test, config_update
from tools.tic_toc import tic, toc
from tools.superscripter import superscripter_uni
from tools.paths import ProjectPaths as PTH


def main():
    tic()
    print("[bright_yellow]mapmaker")

    # check config
    if config_test("regenerate", "freq_maps", "yes"):
        regenerate_all: bool = True
    else:
        regenerate_all: bool = False

    print(f"[green]regenerate_all [white]{regenerate_all}")

    global db_session
    db_session = get_db_session("dpd.db")

    if regenerate_all is False:
        test_inflection_template_changed()
        test_changed_headwords()
        test_html_file_missing()

    else:
        global changed_templates
        global changed_headwords
        global html_file_missing
        changed_templates = []
        changed_headwords = []
        html_file_missing = []

    dicts = make_dfs_and_dicts()
    make_data_dict_and_html(dicts, regenerate_all)
    db_session.close()

    # config update
    config_update("regenerate", "freq_maps", "no")

    toc()


def test_inflection_template_changed():
    print("[green]test if inflection templates changed", end=" ")

    global changed_templates
    try:
        with open(PTH.template_changed_path, "rb") as f:
            changed_templates = pickle.load(f)

            if changed_templates == []:
                print("[white]ok")
            else:
                print(f"[bright_red]{len(changed_templates)}", end=" ")

    except FileNotFoundError as e:
        print(f"[red]{e}")
        changed_templates == []


def test_changed_headwords():
    print("[green]test if stems or patterns have changed", end=" ")

    global changed_headwords
    try:
        with open(PTH.changed_headwords_path, "rb") as f:
            changed_headwords = pickle.load(f)
        if changed_headwords == []:
            print("[white] ok")
        else:
            print(f"[bright_red]{len(changed_headwords)}")

    except FileNotFoundError as e:
        print(f"[bright_red]{e}")
        changed_templates == []


def test_html_file_missing():
    print("[green]test if html file is missing", end=" ")

    idioms_db = db_session.query(
        PaliWord.id, PaliWord.pos
    ).filter(
        PaliWord.pos == "idiom"
    ).all()

    idioms_list = [i.id for i in idioms_db]

    missing_html_db = db_session.query(
        DerivedData.id, DerivedData.freq_html
    ).filter(
        DerivedData.freq_html == "",
        DerivedData.id.notin_(idioms_list)
    ).all()

    global html_file_missing
    html_file_missing = [i.id for i in missing_html_db]

    if len(html_file_missing) > 0:
        print(f"[bright_red]{len(html_file_missing)}")
    else:
        print("ok")


def make_dfs_and_dicts():
    print("[green]making word count dicts and df's")

    wc_dir = PTH.word_count_dir

    vinaya_pārājika_mūla = pd.read_csv(wc_dir.joinpath("vinaya_pārājika_mūla.csv"), sep="\t", header=None)
    vinaya_pārājika_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("vinaya_pārājika_aṭṭhakathā.csv"), sep="\t", header=None)
    vinaya_ṭīkā = pd.read_csv(wc_dir.joinpath("vinaya_ṭīkā.csv"), sep="\t", header=None)
    vinaya_pācittiya_mūla = pd.read_csv(wc_dir.joinpath("vinaya_pācittiya_mūla.csv"), sep="\t", header=None)
    vinaya_pācittiya_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("vinaya_pācittiya_aṭṭhakathā.csv"), sep="\t", header=None)
    vinaya_mahāvagga_mūla = pd.read_csv(wc_dir.joinpath("vinaya_mahāvagga_mūla.csv"), sep="\t", header=None)
    vinaya_mahāvagga_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("vinaya_mahāvagga_aṭṭhakathā.csv"), sep="\t", header=None)
    vinaya_cūḷavagga_mūla = pd.read_csv(wc_dir.joinpath("vinaya_cūḷavagga_mūla.csv"), sep="\t", header=None)
    vinaya_cūḷavagga_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("vinaya_cūḷavagga_aṭṭhakathā.csv"), sep="\t", header=None)
    vinaya_parivāra_mūla = pd.read_csv(wc_dir.joinpath("vinaya_parivāra_mūla.csv"), sep="\t", header=None)
    vinaya_parivāra_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("vinaya_parivāra_aṭṭhakathā.csv"), sep="\t", header=None)
    sutta_dīgha_mūla = pd.read_csv(wc_dir.joinpath("sutta_dīgha_mūla.csv"), sep="\t", header=None)
    sutta_dīgha_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("sutta_dīgha_aṭṭhakathā.csv"), sep="\t", header=None)
    sutta_dīgha_ṭīkā = pd.read_csv(wc_dir.joinpath("sutta_dīgha_ṭīkā.csv"), sep="\t", header=None)
    sutta_majjhima_mūla = pd.read_csv(wc_dir.joinpath("sutta_majjhima_mūla.csv"), sep="\t", header=None)
    sutta_majjhima_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("sutta_majjhima_aṭṭhakathā.csv"), sep="\t", header=None)
    sutta_majjhima_ṭīkā = pd.read_csv(wc_dir.joinpath("sutta_majjhima_ṭīkā.csv"), sep="\t", header=None)
    sutta_saṃyutta_mūla = pd.read_csv(wc_dir.joinpath("sutta_saṃyutta_mūla.csv"), sep="\t", header=None)
    sutta_saṃyutta_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("sutta_saṃyutta_aṭṭhakathā.csv"), sep="\t", header=None)
    sutta_saṃyutta_ṭīkā = pd.read_csv(wc_dir.joinpath("sutta_saṃyutta_ṭīkā.csv"), sep="\t", header=None)
    sutta_aṅguttara_mūla = pd.read_csv(wc_dir.joinpath("sutta_aṅguttara_mūla.csv"), sep="\t", header=None)
    sutta_aṅguttara_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("sutta_aṅguttara_aṭṭhakathā.csv"), sep="\t", header=None)
    sutta_aṅguttara_ṭīkā = pd.read_csv(wc_dir.joinpath("sutta_aṅguttara_ṭīkā.csv"), sep="\t", header=None)
    sutta_khuddaka1_mūla = pd.read_csv(wc_dir.joinpath("sutta_khuddaka1_mūla.csv"), sep="\t", header=None)
    sutta_khuddaka1_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("sutta_khuddaka1_aṭṭhakathā.csv"), sep="\t", header=None)
    sutta_khuddaka2_mūla = pd.read_csv(wc_dir.joinpath("sutta_khuddaka2_mūla.csv"), sep="\t", header=None)
    sutta_khuddaka2_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("sutta_khuddaka2_aṭṭhakathā.csv"), sep="\t", header=None)
    sutta_khuddaka3_mūla = pd.read_csv(wc_dir.joinpath("sutta_khuddaka3_mūla.csv"), sep="\t", header=None)
    sutta_khuddaka3_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("sutta_khuddaka3_aṭṭhakathā.csv"), sep="\t", header=None)
    sutta_khuddaka3_ṭīkā = pd.read_csv(wc_dir.joinpath("sutta_khuddaka3_ṭīkā.csv"), sep="\t", header=None)
    abhidhamma_dhammasaṅgaṇī_mūla = pd.read_csv(wc_dir.joinpath("abhidhamma_dhammasaṅgaṇī_mūla.csv"), sep="\t", header=None)
    abhidhamma_vibhāṅga_mūla = pd.read_csv(wc_dir.joinpath("abhidhamma_vibhāṅga_mūla.csv"), sep="\t", header=None)
    abhidhamma_dhātukathā_mūla = pd.read_csv(wc_dir.joinpath("abhidhamma_dhātukathā_mūla.csv"), sep="\t", header=None)
    abhidhamma_puggalapaññatti_mūla = pd.read_csv(wc_dir.joinpath("abhidhamma_puggalapaññatti_mūla.csv"), sep="\t", header=None)
    abhidhamma_kathāvatthu_mūla = pd.read_csv(wc_dir.joinpath("abhidhamma_kathāvatthu_mūla.csv"), sep="\t", header=None)
    abhidhamma_yamaka_mūla = pd.read_csv(wc_dir.joinpath("abhidhamma_yamaka_mūla.csv"), sep="\t", header=None)
    abhidhamma_paṭṭhāna_mūla = pd.read_csv(wc_dir.joinpath("abhidhamma_paṭṭhāna_mūla.csv"), sep="\t", header=None)
    abhidhamma_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("abhidhamma_aṭṭhakathā.csv"), sep="\t", header=None)
    abhidhamma_ṭīkā = pd.read_csv(wc_dir.joinpath("abhidhamma_ṭīkā.csv"), sep="\t", header=None)
    aññā_visuddhimagga = pd.read_csv(wc_dir.joinpath("aññā_visuddhimagga.csv"), sep="\t", header=None)
    aññā_visuddhimagga_ṭīkā = pd.read_csv(wc_dir.joinpath("aññā_visuddhimagga_ṭīkā.csv"), sep="\t", header=None)
    aññā_leḍī = pd.read_csv(wc_dir.joinpath("aññā_leḍī.csv"), sep="\t", header=None)
    aññā_buddha_vandanā = pd.read_csv(wc_dir.joinpath("aññā_buddha_vandanā.csv"), sep="\t", header=None)
    aññā_vaṃsa = pd.read_csv(wc_dir.joinpath("aññā_vaṃsa.csv"), sep="\t", header=None)
    aññā_byākaraṇa = pd.read_csv(wc_dir.joinpath("aññā_byākaraṇa.csv"), sep="\t", header=None)
    aññā_pucchavisajjana = pd.read_csv(wc_dir.joinpath("aññā_pucchavisajjana.csv"), sep="\t", header=None)
    aññā_nīti = pd.read_csv(wc_dir.joinpath("aññā_nīti.csv"), sep="\t", header=None)
    aññā_pakiṇṇaka = pd.read_csv(wc_dir.joinpath("aññā_pakiṇṇaka.csv"), sep="\t", header=None)
    aññā_sihaḷa = pd.read_csv(wc_dir.joinpath("aññā_sihaḷa.csv"), sep="\t", header=None)

    vinaya_pārājika_mūla_dict = dict(vinaya_pārājika_mūla.values.tolist())
    vinaya_pārājika_aṭṭhakathā_dict = dict(vinaya_pārājika_aṭṭhakathā.values.tolist())
    vinaya_ṭīkā_dict = dict(vinaya_ṭīkā.values.tolist())
    vinaya_pācittiya_mūla_dict = dict(vinaya_pācittiya_mūla.values.tolist())
    vinaya_pācittiya_aṭṭhakathā_dict = dict(vinaya_pācittiya_aṭṭhakathā.values.tolist())
    vinaya_mahāvagga_mūla_dict = dict(vinaya_mahāvagga_mūla.values.tolist())
    vinaya_mahāvagga_aṭṭhakathā_dict = dict(vinaya_mahāvagga_aṭṭhakathā.values.tolist())
    vinaya_cūḷavagga_mūla_dict = dict(vinaya_cūḷavagga_mūla.values.tolist())
    vinaya_cūḷavagga_aṭṭhakathā_dict = dict(vinaya_cūḷavagga_aṭṭhakathā.values.tolist())
    vinaya_parivāra_mūla_dict = dict(vinaya_parivāra_mūla.values.tolist())
    vinaya_parivāra_aṭṭhakathā_dict = dict(vinaya_parivāra_aṭṭhakathā.values.tolist())
    sutta_dīgha_mūla_dict = dict(sutta_dīgha_mūla.values.tolist())
    sutta_dīgha_aṭṭhakathā_dict = dict(sutta_dīgha_aṭṭhakathā.values.tolist())
    sutta_dīgha_ṭīkā_dict = dict(sutta_dīgha_ṭīkā.values.tolist())
    sutta_majjhima_mūla_dict = dict(sutta_majjhima_mūla.values.tolist())
    sutta_majjhima_aṭṭhakathā_dict = dict(sutta_majjhima_aṭṭhakathā.values.tolist())
    sutta_majjhima_ṭīkā_dict = dict(sutta_majjhima_ṭīkā.values.tolist())
    sutta_saṃyutta_mūla_dict = dict(sutta_saṃyutta_mūla.values.tolist())
    sutta_saṃyutta_aṭṭhakathā_dict = dict(sutta_saṃyutta_aṭṭhakathā.values.tolist())
    sutta_saṃyutta_ṭīkā_dict = dict(sutta_saṃyutta_ṭīkā.values.tolist())
    sutta_aṅguttara_mūla_dict = dict(sutta_aṅguttara_mūla.values.tolist())
    sutta_aṅguttara_aṭṭhakathā_dict = dict(sutta_aṅguttara_aṭṭhakathā.values.tolist())
    sutta_aṅguttara_ṭīkā_dict = dict(sutta_aṅguttara_ṭīkā.values.tolist())
    sutta_khuddaka1_mūla_dict = dict(sutta_khuddaka1_mūla.values.tolist())
    sutta_khuddaka1_aṭṭhakathā_dict = dict(sutta_khuddaka1_aṭṭhakathā.values.tolist())
    sutta_khuddaka2_mūla_dict = dict(sutta_khuddaka2_mūla.values.tolist())
    sutta_khuddaka2_aṭṭhakathā_dict = dict(sutta_khuddaka2_aṭṭhakathā.values.tolist())
    sutta_khuddaka3_mūla_dict = dict(sutta_khuddaka3_mūla.values.tolist())
    sutta_khuddaka3_aṭṭhakathā_dict = dict(sutta_khuddaka3_aṭṭhakathā.values.tolist())
    sutta_khuddaka3_ṭīkā_dict = dict(sutta_khuddaka3_ṭīkā.values.tolist())
    abhidhamma_dhammasaṅgaṇī_mūla_dict = dict(abhidhamma_dhammasaṅgaṇī_mūla.values.tolist())
    abhidhamma_vibhāṅga_mūla_dict = dict(abhidhamma_vibhāṅga_mūla.values.tolist())
    abhidhamma_dhātukathā_mūla_dict = dict(abhidhamma_dhātukathā_mūla.values.tolist())
    abhidhamma_puggalapaññatti_mūla_dict = dict(abhidhamma_puggalapaññatti_mūla.values.tolist())
    abhidhamma_kathāvatthu_mūla_dict = dict(abhidhamma_kathāvatthu_mūla.values.tolist())
    abhidhamma_yamaka_mūla_dict = dict(abhidhamma_yamaka_mūla.values.tolist())
    abhidhamma_paṭṭhāna_mūla_dict = dict(abhidhamma_paṭṭhāna_mūla.values.tolist())
    abhidhamma_aṭṭhakathā_dict = dict(abhidhamma_aṭṭhakathā.values.tolist())
    abhidhamma_ṭīkā_dict = dict(abhidhamma_ṭīkā.values.tolist())
    aññā_visuddhimagga_dict = dict(aññā_visuddhimagga.values.tolist())
    aññā_visuddhimagga_ṭīkā_dict = dict(aññā_visuddhimagga_ṭīkā.values.tolist())
    aññā_leḍī_dict = dict(aññā_leḍī.values.tolist())
    aññā_buddha_vandanā_dict = dict(aññā_buddha_vandanā.values.tolist())
    aññā_vaṃsa_dict = dict(aññā_vaṃsa.values.tolist())
    aññā_byākaraṇa_dict = dict(aññā_byākaraṇa.values.tolist())
    aññā_pucchavisajjana_dict = dict(aññā_pucchavisajjana.values.tolist())
    aññā_nīti_dict = dict(aññā_nīti.values.tolist())
    aññā_pakiṇṇaka_dict = dict(aññā_pakiṇṇaka.values.tolist())
    aññā_sihaḷa_dict = dict(aññā_sihaḷa.values.tolist())

    dicts = [
        vinaya_pārājika_mūla_dict,
        vinaya_pārājika_aṭṭhakathā_dict,
        vinaya_ṭīkā_dict,
        vinaya_pācittiya_mūla_dict,
        vinaya_pācittiya_aṭṭhakathā_dict,
        vinaya_mahāvagga_mūla_dict,
        vinaya_mahāvagga_aṭṭhakathā_dict,
        vinaya_cūḷavagga_mūla_dict,
        vinaya_cūḷavagga_aṭṭhakathā_dict,
        vinaya_parivāra_mūla_dict,
        vinaya_parivāra_aṭṭhakathā_dict,
        sutta_dīgha_mūla_dict,
        sutta_dīgha_aṭṭhakathā_dict,
        sutta_dīgha_ṭīkā_dict,
        sutta_majjhima_mūla_dict,
        sutta_majjhima_aṭṭhakathā_dict,
        sutta_majjhima_ṭīkā_dict,
        sutta_saṃyutta_mūla_dict,
        sutta_saṃyutta_aṭṭhakathā_dict,
        sutta_saṃyutta_ṭīkā_dict,
        sutta_aṅguttara_mūla_dict,
        sutta_aṅguttara_aṭṭhakathā_dict,
        sutta_aṅguttara_ṭīkā_dict,
        sutta_khuddaka1_mūla_dict,
        sutta_khuddaka1_aṭṭhakathā_dict,
        sutta_khuddaka2_mūla_dict,
        sutta_khuddaka2_aṭṭhakathā_dict,
        sutta_khuddaka3_mūla_dict,
        sutta_khuddaka3_aṭṭhakathā_dict,
        sutta_khuddaka3_ṭīkā_dict,
        abhidhamma_dhammasaṅgaṇī_mūla_dict,
        abhidhamma_aṭṭhakathā_dict,
        abhidhamma_ṭīkā_dict,
        abhidhamma_vibhāṅga_mūla_dict,
        abhidhamma_dhātukathā_mūla_dict,
        abhidhamma_puggalapaññatti_mūla_dict,
        abhidhamma_kathāvatthu_mūla_dict,
        abhidhamma_yamaka_mūla_dict,
        abhidhamma_paṭṭhāna_mūla_dict,
        aññā_visuddhimagga_dict,
        aññā_visuddhimagga_ṭīkā_dict,
        aññā_leḍī_dict,
        aññā_buddha_vandanā_dict,
        aññā_vaṃsa_dict,
        aññā_byākaraṇa_dict,
        aññā_pucchavisajjana_dict,
        aññā_nīti_dict,
        aññā_pakiṇṇaka_dict,
        aññā_sihaḷa_dict
    ]
    return dicts


def colourme(value, hi, low):
    value = value
    hi = hi
    low = low
    vrange = hi - low
    step = (vrange/9)
    group0 = 0
    group1 = step*1
    group2 = step*2
    group3 = step*3
    group4 = step*4
    group5 = step*5
    group6 = step*6
    group7 = step*7
    group8 = step*8
    group9 = step*9
    group10 = hi

    if value == group0:
        return "gr0"
    elif value > group0 and value <= group1:
        return "gr1"
    elif value > group1 and value <= group2:
        return "gr2"
    elif value > group2 and value <= group3:
        return "gr3"
    elif value > group3 and value <= group4:
        return "gr4"
    elif value > group4 and value <= group5:
        return "gr5"
    elif value > group5 and value <= group6:
        return "gr6"
    elif value > group6 and value <= group7:
        return "gr7"
    elif value > group7 and value <= group8:
        return "gr8"
    elif value > group8 and value < group9:
        return "gr9"
    elif value == group10:
        return "gr10"


def make_data_dict_and_html(dicts, regenerate_all):

    print("[green]compiling data csvs and html")

    dpd_db = db_session.query(PaliWord).all()
    dd_db = db_session.query(DerivedData).all()
    db_length = len(dpd_db)
    add_to_db = []

    indeclinables = ["abbrev", "abs", "ger", "ind", "inf", "prefix", "sandhi", "idiom", "var"]
    conjugations = ["aor", "cond", "fut", "imp", "imperf", "opt", "perf", "pr"]
    declensions = ["adj", "card", "cs", "fem", "letter", "masc", "nt", "ordin", "pp", "pron", "prp", "ptp", "root", "suffix", "ve"]

    for counter, (i, j) in enumerate(zip(dpd_db, dd_db)):

        if i.pos != "idiom" and \
            (i.pattern in changed_templates or
                i.pali_1 in changed_headwords or
                i.id in html_file_missing or
                regenerate_all is True):

            inflections = j.inflections_list

            section = 1
            d = {}
            for dict in dicts:
                count = 0
                for inflection in inflections:
                    if inflection in dict:
                        count += dict.get(inflection)

                d[str(section)] = {"data": count, "class": ""}
                section += 1

            d_values = [v["data"] for k, v, in d.items()]

            value_max = max(d_values)
            value_min = min(d_values)

            for x in d:
                # add class
                d[x]["class"] = colourme(d[x]["data"], value_max, value_min)

                # remove zeros
                if d[x]["data"] == 0:
                    d[x]["data"] = ""

            map_html = ""

            if value_max > 0:

                if i.pos in indeclinables or re.match(r"^!", i.stem):
                    map_html += f"""<p class="heading underlined">Exact matches of the word <b>{superscripter_uni(i.pali_1)}</b> in the Chaṭṭha Saṅgāyana corpus.</p>"""

                elif i.pos in conjugations:
                    map_html += f"""<p class="heading underlined">Exact matches of <b>{superscripter_uni(i.pali_1)} and its conjugations</b> in the Chaṭṭha Saṅgāyana corpus.</p>"""

                elif i.pos in declensions:
                    map_html += f"""<p class="heading underlined">Exact matches of <b>{superscripter_uni(i.pali_1)} and its declensions</b> in the Chaṭṭha Saṅgāyana corpus.</p>"""

                template = Template(filename='frequency/frequency.html')
                map_html += template.render(d=d)

            else:
                map_html += f"""<p class="heading">There are no exact matches of <b>{superscripter_uni(i.pali_1)} or it's inflections</b> in the Chaṭṭha Saṅgāyana corpus.</p>"""
                pass

            add_to_db += [{"id": i.id, "freq_html": map_html}]

            if counter % 5000 == 0:
                print(f"{counter:>10,} / {db_length:<10,} {i.pali_1}")

                with open(
                    PTH.freq_html_dir.joinpath(
                        i.pali_1).with_suffix(".html"), "w") as f:
                    f.write(map_html)

    print("[green]adding to db", end=" ")
    db_session.execute(update(DerivedData), add_to_db)
    db_session.commit()
    db_session.close()
    print(len(add_to_db))


if __name__ == "__main__":
    main()
