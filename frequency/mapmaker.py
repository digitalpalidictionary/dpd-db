#!/usr/bin/env python3.11

import pandas as pd
import pickle
import re
import json

from rich import print
from io import StringIO
from sqlalchemy import update

from helpers import ResourcePaths, get_paths
from db.get_db_session import get_db_session
from db.models import PaliWord, DerivedData
from tools.timeis import tic, toc
from tools.superscripter import superscripter_uni


def main():
    tic()
    print("[bright_yellow]mapmaker")

    global regenerate
    regenerate = False

    print(f"[green]regenerate all [white]{regenerate}")

    global db_session
    db_session = get_db_session("dpd.db")

    global pth
    pth = get_paths()

    test_map_same()
    test_inflection_template_changed()
    test_changed_headwords()
    idioms_list = test_data_file_missing()
    test_html_file_missing(idioms_list)
    dicts = make_dfs_and_dicts()
    wc_data, dpd_db = make_data_dict(dicts)
    generates_html_files(wc_data, dpd_db)
    # make_map_data_json()
    db_session.close()
    toc()


def test_map_same():
    print("[green]test if map has changed", end=" ")

    global map_same
    map_same = False

    new_map = pd.read_csv(
        pth.map_path, sep="\t", index_col=0)

    try:
        with open(pth.old_map_path, "rb") as f:
            old_map = pickle.load(f)
        map_same = new_map.equals(old_map)

        if map_same is False:
            print("[bright_red]changed")
        else:
            print("[white]ok")

    except FileNotFoundError as e:
        print(f"[red]{e}")
        old_map = ""
        map_same = False

    with open(pth.old_map_path, "wb") as f:
        pickle.dump(new_map, f)


def test_inflection_template_changed():
    print("[green]test if inflection templates changed", end=" ")

    global changed_templates
    try:
        with open(pth.template_changed_path, "rb") as f:
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
        with open(pth.changed_headwords_path, "rb") as f:
            changed_headwords = pickle.load(f)
        if changed_headwords == []:
            print("[white] ok")
        else:
            print(f"[bright_red]{len(changed_headwords)}")

    except FileNotFoundError as e:
        print(f"[bright_red]{e}")
        changed_templates == []


def test_data_file_missing():
    print("[green]test if data file is missing", end=" ")

    idioms_db = db_session.query(
        PaliWord.pali_1, PaliWord.pos
    ).filter(
        PaliWord.pos == "idiom"
    ).all()

    idioms_list = [i.pali_1 for i in idioms_db]

    missing_data_db = db_session.query(
        DerivedData.pali_1, DerivedData.freq_data
        ).filter(
            DerivedData.freq_data == "",
            DerivedData.pali_1.notin_(idioms_list)
        ).all()

    global data_file_missing
    data_file_missing = [i.pali_1 for i in missing_data_db]

    if len(data_file_missing) > 0:
        print(f"[bright_red]{len(data_file_missing)}")
    else:
        print("ok")

    return idioms_list


def test_html_file_missing(idioms_list):
    print("[green]test if html file is missing", end=" ")

    missing_html_db = db_session.query(
        DerivedData.pali_1, DerivedData.freq_html
    ).filter(
        DerivedData.freq_html == "",
        DerivedData.pali_1.notin_(idioms_list)
    ).all()

    global html_file_missing
    html_file_missing = [i.pali_1 for i in missing_html_db]

    if len(html_file_missing) > 0:
        print(f"[bright_red]{len(html_file_missing)}")
    else:
        print("ok")


def make_dfs_and_dicts():
    print("[green]making word count dicts and df's")

    wc_dir = pth.word_count_dir

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
    abhidhamma_dhammasaṅgaṇī_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("abhidhamma_dhammasaṅgaṇī_aṭṭhakathā.csv"), sep="\t", header=None)
    abhidhamma_dhammasaṅgaṇī_ṭīkā = pd.read_csv(wc_dir.joinpath("abhidhamma_dhammasaṅgaṇī_ṭīkā.csv"), sep="\t", header=None)
    abhidhamma_vibhāṅga_mūla = pd.read_csv(wc_dir.joinpath("abhidhamma_vibhāṅga_mūla.csv"), sep="\t", header=None)
    abhidhamma_vibhāṅga_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("abhidhamma_vibhāṅga_aṭṭhakathā.csv"), sep="\t", header=None)
    abhidhamma_vibhāṅga_ṭīkā = pd.read_csv(wc_dir.joinpath("abhidhamma_vibhāṅga_ṭīkā.csv"), sep="\t", header=None)
    abhidhamma_dhātukathā_mūla = pd.read_csv(wc_dir.joinpath("abhidhamma_dhātukathā_mūla.csv"), sep="\t", header=None)
    abhidhamma_dhātukathā_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("abhidhamma_dhātukathā_aṭṭhakathā.csv"), sep="\t", header=None)
    abhidhamma_dhātukathā_ṭīkā = pd.read_csv(wc_dir.joinpath("abhidhamma_dhātukathā_ṭīkā.csv"), sep="\t", header=None)
    abhidhamma_puggalapaññatti_mūla = pd.read_csv(wc_dir.joinpath("abhidhamma_puggalapaññatti_mūla.csv"), sep="\t", header=None)
    abhidhamma_puggalapaññatti_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("abhidhamma_puggalapaññatti_aṭṭhakathā.csv"), sep="\t", header=None)
    abhidhamma_puggalapaññatti_ṭīkā = pd.read_csv(wc_dir.joinpath("abhidhamma_puggalapaññatti_ṭīkā.csv"), sep="\t", header=None)
    abhidhamma_kathāvatthu_mūla = pd.read_csv(wc_dir.joinpath("abhidhamma_kathāvatthu_mūla.csv"), sep="\t", header=None)
    abhidhamma_kathāvatthu_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("abhidhamma_kathāvatthu_aṭṭhakathā.csv"), sep="\t", header=None)
    abhidhamma_kathāvatthu_ṭīkā = pd.read_csv(wc_dir.joinpath("abhidhamma_kathāvatthu_ṭīkā.csv"), sep="\t", header=None)
    abhidhamma_yamaka_mūla = pd.read_csv(wc_dir.joinpath("abhidhamma_yamaka_mūla.csv"), sep="\t", header=None)
    abhidhamma_yamaka_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("abhidhamma_yamaka_aṭṭhakathā.csv"), sep="\t", header=None)
    abhidhamma_yamaka_ṭīkā = pd.read_csv(wc_dir.joinpath("abhidhamma_yamaka_ṭīkā.csv"), sep="\t", header=None)
    abhidhamma_paṭṭhāna_mūla = pd.read_csv(wc_dir.joinpath("abhidhamma_paṭṭhāna_mūla.csv"), sep="\t", header=None)
    abhidhamma_paṭṭhāna_aṭṭhakathā = pd.read_csv(wc_dir.joinpath("abhidhamma_paṭṭhāna_aṭṭhakathā.csv"), sep="\t", header=None)
    abhidhamma_paṭṭhāna_ṭīkā = pd.read_csv(wc_dir.joinpath("abhidhamma_paṭṭhāna_ṭīkā.csv"), sep="\t", header=None)
    abhidhamma_aññā_ṭīkā = pd.read_csv(wc_dir.joinpath("abhidhamma_aññā_ṭīkā.csv"), sep="\t", header=None)
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
    abhidhamma_dhammasaṅgaṇī_aṭṭhakathā_dict = dict(abhidhamma_dhammasaṅgaṇī_aṭṭhakathā.values.tolist())
    abhidhamma_dhammasaṅgaṇī_ṭīkā_dict = dict(abhidhamma_dhammasaṅgaṇī_ṭīkā.values.tolist())
    abhidhamma_vibhāṅga_mūla_dict = dict(abhidhamma_vibhāṅga_mūla.values.tolist())
    abhidhamma_vibhāṅga_aṭṭhakathā_dict = dict(abhidhamma_vibhāṅga_aṭṭhakathā.values.tolist())
    abhidhamma_vibhāṅga_ṭīkā_dict = dict(abhidhamma_vibhāṅga_ṭīkā.values.tolist())
    abhidhamma_dhātukathā_mūla_dict = dict(abhidhamma_dhātukathā_mūla.values.tolist())
    abhidhamma_dhātukathā_aṭṭhakathā_dict = dict(abhidhamma_dhātukathā_aṭṭhakathā.values.tolist())
    abhidhamma_dhātukathā_ṭīkā_dict = dict(abhidhamma_dhātukathā_ṭīkā.values.tolist())
    abhidhamma_puggalapaññatti_mūla_dict = dict(abhidhamma_puggalapaññatti_mūla.values.tolist())
    abhidhamma_puggalapaññatti_aṭṭhakathā_dict = dict(abhidhamma_puggalapaññatti_aṭṭhakathā.values.tolist())
    abhidhamma_puggalapaññatti_ṭīkā_dict = dict(abhidhamma_puggalapaññatti_ṭīkā.values.tolist())
    abhidhamma_kathāvatthu_mūla_dict = dict(abhidhamma_kathāvatthu_mūla.values.tolist())
    abhidhamma_kathāvatthu_aṭṭhakathā_dict = dict(abhidhamma_kathāvatthu_aṭṭhakathā.values.tolist())
    abhidhamma_kathāvatthu_ṭīkā_dict = dict(abhidhamma_kathāvatthu_ṭīkā.values.tolist())
    abhidhamma_yamaka_mūla_dict = dict(abhidhamma_yamaka_mūla.values.tolist())
    abhidhamma_yamaka_aṭṭhakathā_dict = dict(abhidhamma_yamaka_aṭṭhakathā.values.tolist())
    abhidhamma_yamaka_ṭīkā_dict = dict(abhidhamma_yamaka_ṭīkā.values.tolist())
    abhidhamma_paṭṭhāna_mūla_dict = dict(abhidhamma_paṭṭhāna_mūla.values.tolist())
    abhidhamma_paṭṭhāna_aṭṭhakathā_dict = dict(abhidhamma_paṭṭhāna_aṭṭhakathā.values.tolist())
    abhidhamma_paṭṭhāna_ṭīkā_dict = dict(abhidhamma_paṭṭhāna_ṭīkā.values.tolist())
    abhidhamma_aññā_ṭīkā_dict = dict(abhidhamma_aññā_ṭīkā.values.tolist())
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
        abhidhamma_dhammasaṅgaṇī_aṭṭhakathā_dict,
        abhidhamma_dhammasaṅgaṇī_ṭīkā_dict,
        abhidhamma_vibhāṅga_mūla_dict,
        abhidhamma_vibhāṅga_aṭṭhakathā_dict,
        abhidhamma_vibhāṅga_ṭīkā_dict,
        abhidhamma_dhātukathā_mūla_dict,
        abhidhamma_dhātukathā_aṭṭhakathā_dict,
        abhidhamma_dhātukathā_ṭīkā_dict,
        abhidhamma_puggalapaññatti_mūla_dict,
        abhidhamma_puggalapaññatti_aṭṭhakathā_dict,
        abhidhamma_puggalapaññatti_ṭīkā_dict,
        abhidhamma_kathāvatthu_mūla_dict,
        abhidhamma_kathāvatthu_aṭṭhakathā_dict,
        abhidhamma_kathāvatthu_ṭīkā_dict,
        abhidhamma_yamaka_mūla_dict,
        abhidhamma_yamaka_aṭṭhakathā_dict,
        abhidhamma_yamaka_ṭīkā_dict,
        abhidhamma_paṭṭhāna_mūla_dict,
        abhidhamma_paṭṭhāna_aṭṭhakathā_dict,
        abhidhamma_paṭṭhāna_ṭīkā_dict,
        abhidhamma_aññā_ṭīkā_dict,
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


def make_data_dict(dicts):

    print("[green]compiling data csvs")
    errorlog = []

    dpd_db = db_session.query(PaliWord).all()
    db_length = len(dpd_db)
    wc_data = {}
    add_to_db = []

    for counter, i in enumerate(dpd_db):

        if i.pos != "idiom" and \
            (map_same is False or
                i.pattern in changed_templates or
                i.pali_1 in changed_headwords or
                i.pali_1 in data_file_missing or
                i.pali_1 in html_file_missing or
                regenerate is True):

            if regenerate is True:
                if counter % 10000 == 0:
                    print(f"{counter:>10,} / {db_length:<10,} {i.pali_1}")
            else:
                if counter % 5000 == 0:
                    print(f"{counter:>10,} / {db_length:<10,} {i.pali_1}")

            # output_file = open(f"output/data/{headword}.csv", "w")
            try:
                word = db_session.query(
                    DerivedData.inflections
                    ).filter(
                        DerivedData.pali_1 == i.pali_1
                        ).first()

                inflections = json.loads(word.inflections)

            except Exception:
                print(f"[red]{i.pali_1} error! why!?")
                errorlog.append(i.pali_1)

            section = 0
            data = ""
            for dict in dicts:
                count = 0
                for inflection in inflections:
                    if inflection in dict:
                        count += dict.get(inflection)

                data += f"{section},{count}\n"
                section += 1

            wc_data[i.pali_1] = data
            add_to_db += [{"id": i.id, "freq_data": data}]

    print("[green]adding to db", end=" ")
    db_session.execute(update(DerivedData), add_to_db)
    db_session.commit()
    print(len(add_to_db))

    if len(errorlog) != 0:
        print(f"[red]file read errors {errorlog} {len(errorlog)}")

    return wc_data, dpd_db


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
    html = ""

    if value == group0:
        html = "<td class='gr0'>⠀</td>"
    elif value > group0 and value <= group1:
        html = f"<td class='gr1'>{value}</td>"
    elif value > group1 and value <= group2:
        html = f"<td class='gr2'>{value}</td>"
    elif value > group2 and value <= group3:
        html = f"<td class='gr3'>{value}</td>"
    elif value > group3 and value <= group4:
        html = f"<td class='gr4'>{value}</td>"
    elif value > group4 and value <= group5:
        html = f"<td class='gr5'>{value}</td>"
    elif value > group5 and value <= group6:
        html = f"<td class='gr6'>{value}</td>"
    elif value > group6 and value <= group7:
        html = f"<td class='gr7'>{value}</td>"
    elif value > group7 and value <= group8:
        html = f"<td class='gr8'>{value}</td>"
    elif value > group8 and value < group9:
        html = f"<td class='gr9'>{value}</td>"
    elif value == group10:
        html = f"<td class='gr10'>{value}</td>"

    return html


def generates_html_files(wc_data, dpd_db):
    print("[green]generating html files")
    template = pd.read_csv(pth.map_path, sep="\t", index_col=0)

    indeclinables = ["abbrev", "abs", "ger", "ind", "inf", "prefix", "sandhi", "idiom", "var"]
    conjugations = ["aor", "cond", "fut", "imp", "imperf", "opt", "perf", "pr"]
    declensions = ["adj", "card", "cs", "fem", "letter", "masc", "nt", "ordin", "pp", "pron", "prp", "ptp", "root", "suffix", "ve"]

    length = len(dpd_db)
    add_to_db = []

    for counter, i in enumerate(dpd_db):

        if i.pos != "idiom" and \
            (map_same is False or
                i.pattern in changed_templates or
                i.pali_1 in changed_headwords or
                i.pali_1 in data_file_missing or
                i.pali_1 in html_file_missing or
                regenerate is True):

            try:
                data = pd.read_csv(
                    StringIO(wc_data[i.pali_1]), sep=",",
                    index_col=0, header=None, dtype=int)

            except KeyError:
                print(f"[bright_red]data not found for [red]{i.pali_1}")

            if regenerate is True:
                if counter % 10000 == 0:
                    print(f"{counter:>10,} / {length:<10,} {i.pali_1}")
            else:
                if counter % 5000 == 0:
                    print(f"{counter:>10,} / {length:<10,} {i.pali_1}")

            value_max = data[1].max()
            value_min = data[1].min()

            vinaya_pārājika_mūla = data.iloc[0, 0]
            vinaya_pārājika_aṭṭhakathā = data.iloc[1, 0]
            vinaya_ṭīkā = data.iloc[2, 0]
            vinaya_pācittiya_mūla = data.iloc[3, 0]
            vinaya_pācittiya_aṭṭhakathā = data.iloc[4, 0]
            vinaya_mahāvagga_mūla = data.iloc[5, 0]
            vinaya_mahāvagga_aṭṭhakathā = data.iloc[6, 0]
            vinaya_cūḷavagga_mūla = data.iloc[7, 0]
            vinaya_cūḷavagga_aṭṭhakathā = data.iloc[8, 0]
            vinaya_parivāra_mūla = data.iloc[9, 0]
            vinaya_parivāra_aṭṭhakathā = data.iloc[10, 0]
            sutta_dīgha_mūla = data.iloc[11, 0]
            sutta_dīgha_aṭṭhakathā = data.iloc[12, 0]
            sutta_dīgha_ṭīkā = data.iloc[13, 0]
            sutta_majjhima_mūla = data.iloc[14, 0]
            sutta_majjhima_aṭṭhakathā = data.iloc[15, 0]
            sutta_majjhima_ṭīkā = data.iloc[16, 0]
            sutta_saṃyutta_mūla = data.iloc[17, 0]
            sutta_saṃyutta_aṭṭhakathā = data.iloc[18, 0]
            sutta_saṃyutta_ṭīkā = data.iloc[19, 0]
            sutta_aṅguttara_mūla = data.iloc[20, 0]
            sutta_aṅguttara_aṭṭhakathā = data.iloc[21, 0]
            sutta_aṅguttara_ṭīkā = data.iloc[22, 0]
            sutta_khuddaka1_mūla = data.iloc[23, 0]
            sutta_khuddaka1_aṭṭhakathā = data.iloc[24, 0]
            sutta_khuddaka2_mūla = data.iloc[25, 0]
            sutta_khuddaka2_aṭṭhakathā = data.iloc[26, 0]
            sutta_khuddaka3_mūla = data.iloc[27, 0]
            sutta_khuddaka3_aṭṭhakathā = data.iloc[28, 0]
            sutta_khuddaka3_ṭīkā = data.iloc[29, 0]
            abhidhamma_dhammasaṅgaṇī_mūla = data.iloc[30, 0]
            abhidhamma_dhammasaṅgaṇī_aṭṭhakathā = data.iloc[31, 0]
            abhidhamma_dhammasaṅgaṇī_ṭīkā = data.iloc[32, 0]
            abhidhamma_vibhāṅga_mūla = data.iloc[33, 0]
            abhidhamma_vibhāṅga_aṭṭhakathā = data.iloc[34, 0]
            abhidhamma_vibhāṅga_ṭīkā = data.iloc[35, 0]
            abhidhamma_dhātukathā_mūla = data.iloc[36, 0]
            abhidhamma_dhātukathā_aṭṭhakathā = data.iloc[37, 0]
            abhidhamma_dhātukathā_ṭīkā = data.iloc[38, 0]
            abhidhamma_puggalapaññatti_mūla = data.iloc[39, 0]
            abhidhamma_puggalapaññatti_aṭṭhakathā = data.iloc[40, 0]
            abhidhamma_puggalapaññatti_ṭīkā = data.iloc[41, 0]
            abhidhamma_kathāvatthu_mūla = data.iloc[42, 0]
            abhidhamma_kathāvatthu_aṭṭhakathā = data.iloc[43, 0]
            abhidhamma_kathāvatthu_ṭīkā = data.iloc[44, 0]
            abhidhamma_yamaka_mūla = data.iloc[45, 0]
            abhidhamma_yamaka_aṭṭhakathā = data.iloc[46, 0]
            abhidhamma_yamaka_ṭīkā = data.iloc[47, 0]
            abhidhamma_paṭṭhāna_mūla = data.iloc[48, 0]
            abhidhamma_paṭṭhāna_aṭṭhakathā = data.iloc[49, 0]
            abhidhamma_paṭṭhāna_ṭīkā = data.iloc[50, 0]
            abhidhamma_aññā_ṭīkā = data.iloc[51, 0]
            aññā_visuddhimagga = data.iloc[52, 0]
            aññā_visuddhimagga_ṭīkā = data.iloc[53, 0]
            aññā_leḍī = data.iloc[54, 0]
            aññā_buddha_vandanā = data.iloc[55, 0]
            aññā_vaṃsa = data.iloc[56, 0]
            aññā_byākaraṇa = data.iloc[57, 0]
            aññā_pucchavisajjana = data.iloc[58, 0]
            aññā_nīti = data.iloc[59, 0]
            aññā_pakiṇṇaka = data.iloc[60, 0]
            aññā_sihaḷa = data.iloc[61, 0]

            vinaya_pārājika_mūla = colourme(vinaya_pārājika_mūla, value_max, value_min)
            vinaya_pārājika_aṭṭhakathā = colourme(vinaya_pārājika_aṭṭhakathā, value_max, value_min)
            vinaya_ṭīkā = colourme(vinaya_ṭīkā, value_max, value_min)
            vinaya_pācittiya_mūla = colourme(vinaya_pācittiya_mūla, value_max, value_min)
            vinaya_pācittiya_aṭṭhakathā = colourme(vinaya_pācittiya_aṭṭhakathā, value_max, value_min)
            vinaya_mahāvagga_mūla = colourme(vinaya_mahāvagga_mūla, value_max, value_min)
            vinaya_mahāvagga_aṭṭhakathā = colourme(vinaya_mahāvagga_aṭṭhakathā, value_max, value_min)
            vinaya_cūḷavagga_mūla = colourme(vinaya_cūḷavagga_mūla, value_max, value_min)
            vinaya_cūḷavagga_aṭṭhakathā = colourme(vinaya_cūḷavagga_aṭṭhakathā, value_max, value_min)
            vinaya_parivāra_mūla = colourme(vinaya_parivāra_mūla, value_max, value_min)
            vinaya_parivāra_aṭṭhakathā = colourme(vinaya_parivāra_aṭṭhakathā, value_max, value_min)
            sutta_dīgha_mūla = colourme(sutta_dīgha_mūla, value_max, value_min)
            sutta_dīgha_aṭṭhakathā = colourme(sutta_dīgha_aṭṭhakathā, value_max, value_min)
            sutta_dīgha_ṭīkā = colourme(sutta_dīgha_ṭīkā, value_max, value_min)
            sutta_majjhima_mūla = colourme(sutta_majjhima_mūla, value_max, value_min)
            sutta_majjhima_aṭṭhakathā = colourme(sutta_majjhima_aṭṭhakathā, value_max, value_min)
            sutta_majjhima_ṭīkā = colourme(sutta_majjhima_ṭīkā, value_max, value_min)
            sutta_saṃyutta_mūla = colourme(sutta_saṃyutta_mūla, value_max, value_min)
            sutta_saṃyutta_aṭṭhakathā = colourme(sutta_saṃyutta_aṭṭhakathā, value_max, value_min)
            sutta_saṃyutta_ṭīkā = colourme(sutta_saṃyutta_ṭīkā, value_max, value_min)
            sutta_aṅguttara_mūla = colourme(sutta_aṅguttara_mūla, value_max, value_min)
            sutta_aṅguttara_aṭṭhakathā = colourme(sutta_aṅguttara_aṭṭhakathā, value_max, value_min)
            sutta_aṅguttara_ṭīkā = colourme(sutta_aṅguttara_ṭīkā, value_max, value_min)
            sutta_khuddaka1_mūla = colourme(sutta_khuddaka1_mūla, value_max, value_min)
            sutta_khuddaka1_aṭṭhakathā = colourme(sutta_khuddaka1_aṭṭhakathā, value_max, value_min)
            sutta_khuddaka2_mūla = colourme(sutta_khuddaka2_mūla, value_max, value_min)
            sutta_khuddaka2_aṭṭhakathā = colourme(sutta_khuddaka2_aṭṭhakathā, value_max, value_min)
            sutta_khuddaka3_mūla = colourme(sutta_khuddaka3_mūla, value_max, value_min)
            sutta_khuddaka3_aṭṭhakathā = colourme(sutta_khuddaka3_aṭṭhakathā, value_max, value_min)
            sutta_khuddaka3_ṭīkā = colourme(sutta_khuddaka3_ṭīkā, value_max, value_min)
            abhidhamma_dhammasaṅgaṇī_mūla = colourme(abhidhamma_dhammasaṅgaṇī_mūla, value_max, value_min)
            abhidhamma_dhammasaṅgaṇī_aṭṭhakathā = colourme(abhidhamma_dhammasaṅgaṇī_aṭṭhakathā, value_max, value_min)
            abhidhamma_dhammasaṅgaṇī_ṭīkā = colourme(abhidhamma_dhammasaṅgaṇī_ṭīkā, value_max, value_min)
            abhidhamma_vibhāṅga_mūla = colourme(abhidhamma_vibhāṅga_mūla, value_max, value_min)
            abhidhamma_vibhāṅga_aṭṭhakathā = colourme(abhidhamma_vibhāṅga_aṭṭhakathā, value_max, value_min)
            abhidhamma_vibhāṅga_ṭīkā = colourme(abhidhamma_vibhāṅga_ṭīkā, value_max, value_min)
            abhidhamma_dhātukathā_mūla = colourme(abhidhamma_dhātukathā_mūla, value_max, value_min)
            abhidhamma_dhātukathā_aṭṭhakathā = colourme(abhidhamma_dhātukathā_aṭṭhakathā, value_max, value_min)
            abhidhamma_dhātukathā_ṭīkā = colourme(abhidhamma_dhātukathā_ṭīkā, value_max, value_min)
            abhidhamma_puggalapaññatti_mūla = colourme(abhidhamma_puggalapaññatti_mūla, value_max, value_min)
            abhidhamma_puggalapaññatti_aṭṭhakathā = colourme(abhidhamma_puggalapaññatti_aṭṭhakathā, value_max, value_min)
            abhidhamma_puggalapaññatti_ṭīkā = colourme(abhidhamma_puggalapaññatti_ṭīkā, value_max, value_min)
            abhidhamma_kathāvatthu_mūla = colourme(abhidhamma_kathāvatthu_mūla, value_max, value_min)
            abhidhamma_kathāvatthu_aṭṭhakathā = colourme(abhidhamma_kathāvatthu_aṭṭhakathā, value_max, value_min)
            abhidhamma_kathāvatthu_ṭīkā = colourme(abhidhamma_kathāvatthu_ṭīkā, value_max, value_min)
            abhidhamma_yamaka_mūla = colourme(abhidhamma_yamaka_mūla, value_max, value_min)
            abhidhamma_yamaka_aṭṭhakathā = colourme(abhidhamma_yamaka_aṭṭhakathā, value_max, value_min)
            abhidhamma_yamaka_ṭīkā = colourme(abhidhamma_yamaka_ṭīkā, value_max, value_min)
            abhidhamma_paṭṭhāna_mūla = colourme(abhidhamma_paṭṭhāna_mūla, value_max, value_min)
            abhidhamma_paṭṭhāna_aṭṭhakathā = colourme(abhidhamma_paṭṭhāna_aṭṭhakathā, value_max, value_min)
            abhidhamma_paṭṭhāna_ṭīkā = colourme(abhidhamma_paṭṭhāna_ṭīkā, value_max, value_min)
            abhidhamma_aññā_ṭīkā = colourme(abhidhamma_aññā_ṭīkā, value_max, value_min)
            aññā_visuddhimagga = colourme(aññā_visuddhimagga, value_max, value_min)
            aññā_visuddhimagga_ṭīkā = colourme(aññā_visuddhimagga_ṭīkā, value_max, value_min)
            aññā_leḍī = colourme(aññā_leḍī, value_max, value_min)
            aññā_buddha_vandanā = colourme(aññā_buddha_vandanā, value_max, value_min)
            aññā_vaṃsa = colourme(aññā_vaṃsa, value_max, value_min)
            aññā_byākaraṇa = colourme(aññā_byākaraṇa, value_max, value_min)
            aññā_pucchavisajjana = colourme(aññā_pucchavisajjana, value_max, value_min)
            aññā_nīti = colourme(aññā_nīti, value_max, value_min)
            aññā_pakiṇṇaka = colourme(aññā_pakiṇṇaka, value_max, value_min)
            aññā_sihaḷa = colourme(aññā_sihaḷa, value_max, value_min)

            freq_map = template

            freq_map.iloc[0,0] = vinaya_pārājika_mūla
            freq_map.iloc[0,1] = vinaya_pārājika_aṭṭhakathā
            freq_map.iloc[0,2] = vinaya_ṭīkā
            freq_map.iloc[1,0] = vinaya_pācittiya_mūla
            freq_map.iloc[1,1] = vinaya_pācittiya_aṭṭhakathā
            freq_map.iloc[2,0] = vinaya_mahāvagga_mūla
            freq_map.iloc[2,1] = vinaya_mahāvagga_aṭṭhakathā
            freq_map.iloc[3,0] = vinaya_cūḷavagga_mūla
            freq_map.iloc[3,1] = vinaya_cūḷavagga_aṭṭhakathā
            freq_map.iloc[4,0] = vinaya_parivāra_mūla
            freq_map.iloc[4,1] = vinaya_parivāra_aṭṭhakathā
            freq_map.iloc[5,0] = sutta_dīgha_mūla
            freq_map.iloc[5,1] = sutta_dīgha_aṭṭhakathā
            freq_map.iloc[5,2] = sutta_dīgha_ṭīkā
            freq_map.iloc[6,0] = sutta_majjhima_mūla
            freq_map.iloc[6,1] = sutta_majjhima_aṭṭhakathā
            freq_map.iloc[6,2] = sutta_majjhima_ṭīkā
            freq_map.iloc[7,0] = sutta_saṃyutta_mūla
            freq_map.iloc[7,1] = sutta_saṃyutta_aṭṭhakathā
            freq_map.iloc[7,2] = sutta_saṃyutta_ṭīkā
            freq_map.iloc[8,0] = sutta_aṅguttara_mūla
            freq_map.iloc[8,1] = sutta_aṅguttara_aṭṭhakathā
            freq_map.iloc[8,2] = sutta_aṅguttara_ṭīkā
            freq_map.iloc[9,0] = sutta_khuddaka1_mūla
            freq_map.iloc[9,1] = sutta_khuddaka1_aṭṭhakathā
            freq_map.iloc[10,0] = sutta_khuddaka2_mūla
            freq_map.iloc[10,1] = sutta_khuddaka2_aṭṭhakathā
            freq_map.iloc[11,0] = sutta_khuddaka3_mūla
            freq_map.iloc[11,1] = sutta_khuddaka3_aṭṭhakathā
            freq_map.iloc[11,2] = sutta_khuddaka3_ṭīkā
            freq_map.iloc[12,0] = abhidhamma_dhammasaṅgaṇī_mūla
            freq_map.iloc[12,1] = abhidhamma_dhammasaṅgaṇī_aṭṭhakathā
            freq_map.iloc[12,2] = abhidhamma_dhammasaṅgaṇī_ṭīkā
            freq_map.iloc[13,0] = abhidhamma_vibhāṅga_mūla
            freq_map.iloc[13,1] = abhidhamma_vibhāṅga_aṭṭhakathā
            freq_map.iloc[13,2] = abhidhamma_vibhāṅga_ṭīkā
            freq_map.iloc[14,0] = abhidhamma_dhātukathā_mūla
            freq_map.iloc[14,1] = abhidhamma_dhātukathā_aṭṭhakathā
            freq_map.iloc[14,2] = abhidhamma_dhātukathā_ṭīkā
            freq_map.iloc[15,0] = abhidhamma_puggalapaññatti_mūla
            freq_map.iloc[15,1] = abhidhamma_puggalapaññatti_aṭṭhakathā
            freq_map.iloc[15,2] = abhidhamma_puggalapaññatti_ṭīkā
            freq_map.iloc[16,0] = abhidhamma_kathāvatthu_mūla
            freq_map.iloc[16,1] = abhidhamma_kathāvatthu_aṭṭhakathā
            freq_map.iloc[16,2] = abhidhamma_kathāvatthu_ṭīkā
            freq_map.iloc[17,0] = abhidhamma_yamaka_mūla
            freq_map.iloc[17,1] = abhidhamma_yamaka_aṭṭhakathā
            freq_map.iloc[17,2] = abhidhamma_yamaka_ṭīkā
            freq_map.iloc[18,0] = abhidhamma_paṭṭhāna_mūla
            freq_map.iloc[18,1] = abhidhamma_paṭṭhāna_aṭṭhakathā
            freq_map.iloc[18,2] = abhidhamma_paṭṭhāna_ṭīkā
            freq_map.iloc[19,2] = abhidhamma_aññā_ṭīkā
            freq_map.iloc[20,1] = aññā_visuddhimagga
            freq_map.iloc[20,2] = aññā_visuddhimagga_ṭīkā
            freq_map.iloc[21,2] = aññā_leḍī
            freq_map.iloc[22,2] = aññā_buddha_vandanā
            freq_map.iloc[23,2] = aññā_vaṃsa
            freq_map.iloc[24,2] = aññā_byākaraṇa
            freq_map.iloc[25,2] = aññā_pucchavisajjana
            freq_map.iloc[26,2] = aññā_nīti
            freq_map.iloc[27,2] = aññā_pakiṇṇaka
            freq_map.iloc[28,2] = aññā_sihaḷa

            freq_map.fillna(0, inplace=True)
            
            map_html = ""
            # pali_clean = re.sub(r" \d.*$", "", i.pali_1)

            if value_max > 0:

                if i.pos in indeclinables or re.match(r"^!", i.stem):
                    map_html += f"""<p class="heading underlined">Exact matches of the word <b>{superscripter_uni(i.pali_1)}</b> in the Chaṭṭha Saṅgāyana corpus.</p>"""
                    
                elif i.pos in conjugations:
                    map_html += f"""<p class="heading underlined">Exact matches of <b>{superscripter_uni(i.pali_1)} and its conjugations</b> in the Chaṭṭha Saṅgāyana corpus.</p>"""
                
                elif i.pos in declensions:
                    map_html += f"""<p class="heading underlined">Exact matches of <b>{superscripter_uni(i.pali_1)} and its declensions</b> in the Chaṭṭha Saṅgāyana corpus.</p>"""

                # map_html += f"""<style>{css}</style>"""
                
                freq_map = freq_map.astype(str)
                map_html += freq_map.to_html(escape=False)
                map_html = re.sub('<tr style="text-align: right;>"', "<tr>", map_html)
                map_html = re.sub("<td><td>", "<td>", map_html)
                map_html = re.sub("<td><td", "<td", map_html)
                map_html = re.sub("</td></td>", "</td>", map_html)
                map_html = re.sub('<table border="1" class="dataframe">', "<table class = 'freq'>", map_html)
                map_html = re.sub("<td>-1</td>", "<td class='void'></td>", map_html)

                # add lines

                map_html = re.sub(r"""<tr>
    <th>Sutta Dīgha Nikāya</th>""",
        """<tr class="line">
    <th>Sutta Dīgha Nikāya</th>""",
                    map_html)
                
                map_html = re.sub(r"""<tr>
    <th>Abhidhamma Dhammasaṅgaṇī</th>""", 
                    """<tr class="line">
    <th>Abhidhamma Dhammasaṅgaṇī</th>""",
                    map_html)

                map_html = re.sub(r"""<tr>
    <th>Aññā Abhidhamma</th>""",
                    """<tr class="line">
    <th>Aññā Abhidhamma</th>""",
                    map_html)       

            else:
                map_html += f"""<p class="heading">There are no exact matches of <b>{superscripter_uni(i.pali_1)} or it's inflections</b> in the Chaṭṭha Saṅgāyana corpus.</p>"""
                pass

            with open(f"frequency/output/html/{i.pali_1}.html", "w") as f:
                f.write(map_html)
            
            add_to_db += [{"id": i.id, "freq_html": map_html}]
    
    print("[green]adding to db", end=" ")
    db_session.execute(update(DerivedData), add_to_db)
    db_session.commit()
    print(len(add_to_db))


# def make_map_data_json():
#     """compile data files for json export to other apps"""
#     print(f"[green]compiling data files to json")
    
#     file_dir = "output/data/"
#     data_dict = {}
#     counter = 0
    
#     for root, dirs, files in os.walk(file_dir, topdown=True):
#         files_len = len(files)
#         for file_name in files:
#             file_name_clean = file_name.replace(".csv", "")

#             if counter %5000 ==0:
#                 print(f"{white}{counter}/{files_len}\t{file_name_clean}")
            
#             with open(f"{file_dir}{file_name}") as infile:
#                 reader = csv.reader(infile)
#                 data_dict[file_name_clean] = {rows[0]: int(rows[1]) for rows in reader}

#             counter += 1

#     data_json = json.dumps(data_dict, ensure_ascii=False, indent=4)
#     with open("../dpd-app/data/frequency-data.json", "w") as f:
#         f.write(data_json)


if __name__ == "__main__":
    main()