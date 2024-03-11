#!/usr/bin/env python3

"""Creates a word frequency file for every book in
VRI Chaṭṭha Saṅgāyana Tipiṭaka."""

import nltk
import pandas as pd
import os

from rich import print
from tools.clean_machine import clean_machine
from tools.pali_text_files import ebts
from tools.paths import ProjectPaths
nltk.download('punkt')


def main():
    """Do the job."""
    print("[bright_yellow]generating text lists")
    pth = ProjectPaths()
    make_tipitaka_dict(pth)


def make_tipitaka_dict(pth: ProjectPaths):
    """Assign the files related to each section of the Tipiṭaka into a dictionary."""
    print("[green]making master dict", end=" ")
    tipitaka_dict = {}

    # !!! is it possible
    # !!! to combine this with
    # !!! the list of text for sandhi splitting?

    # vinaya

    vinaya_pārājika_mūla = ["vin01m.mul.txt"]
    vinaya_pārājika_aṭṭhakathā = ["vin01a.att.txt"]
    vinaya_ṭīkā = ["vin01t1.tik.txt", "vin01t2.tik.txt", "vin02t.tik.txt", "vin04t.nrf.txt", "vin05t.nrf.txt", "vin06t.nrf.txt", "vin07t.nrf.txt", "vin08t.nrf.txt", "vin09t.nrf.txt", "vin10t.nrf.txt", "vin11t.nrf.txt", "vin12t.nrf.txt", "vin13t.nrf.txt"]

    tipitaka_dict["vinaya_pārājika_mūla"] = vinaya_pārājika_mūla
    tipitaka_dict["vinaya_pārājika_aṭṭhakathā"] = vinaya_pārājika_aṭṭhakathā
    tipitaka_dict["vinaya_ṭīkā"] = vinaya_ṭīkā

    vinaya_pācittiya_mūla = ["vin02m1.mul.txt"]
    vinaya_pācittiya_aṭṭhakathā = ["vin02a1.att.txt"]

    tipitaka_dict["vinaya_pācittiya_mūla"] = vinaya_pācittiya_mūla
    tipitaka_dict["vinaya_pācittiya_aṭṭhakathā"] = vinaya_pācittiya_aṭṭhakathā

    vinaya_mahāvagga_mūla = ["vin02m2.mul.txt"]
    vinaya_mahāvagga_aṭṭhakathā = ["vin02a2.att.txt"]

    tipitaka_dict["vinaya_mahāvagga_mūla"] = vinaya_mahāvagga_mūla
    tipitaka_dict["vinaya_mahāvagga_aṭṭhakathā"] = vinaya_mahāvagga_aṭṭhakathā

    vinaya_cūḷavagga_mūla = ["vin02m3.mul.txt"]
    vinaya_cūḷavagga_aṭṭhakathā = ["vin02a3.att.txt"]

    tipitaka_dict["vinaya_cūḷavagga_mūla"] = vinaya_cūḷavagga_mūla
    tipitaka_dict["vinaya_cūḷavagga_aṭṭhakathā"] = vinaya_cūḷavagga_aṭṭhakathā

    vinaya_parivāra_mūla = ["vin02m4.mul.txt"]
    vinaya_parivāra_aṭṭhakathā = ["vin02a4.att.txt"]

    tipitaka_dict["vinaya_parivāra_mūla"] = vinaya_parivāra_mūla
    tipitaka_dict["vinaya_parivāra_aṭṭhakathā"] = vinaya_parivāra_aṭṭhakathā

    # sutta

    # dīgha

    sutta_dīgha_mūla = ["s0101m.mul.txt", "s0102m.mul.txt", "s0103m.mul.txt"]
    sutta_dīgha_aṭṭhakathā = ["s0101a.att.txt", "s0102a.att.txt", "s0103a.att.txt"]
    sutta_dīgha_ṭīkā = ["s0101t.tik.txt", "s0102t.tik.txt", "s0103t.tik.txt", "s0104t.nrf.txt", "s0105t.nrf.txt"]

    tipitaka_dict["sutta_dīgha_mūla"] = sutta_dīgha_mūla
    tipitaka_dict["sutta_dīgha_aṭṭhakathā"] = sutta_dīgha_aṭṭhakathā
    tipitaka_dict["sutta_dīgha_ṭīkā"] = sutta_dīgha_ṭīkā

    # majjhima

    sutta_majjhima_mūla = ["s0201m.mul.txt", "s0202m.mul.txt", "s0203m.mul.txt"]
    sutta_majjhima_aṭṭhakathā = ["s0201a.att.txt", "s0202a.att.txt", "s0203a.att.txt"]
    sutta_majjhima_ṭīkā = ["s0201t.tik.txt", "s0202t.tik.txt", "s0203t.tik.txt"]

    tipitaka_dict["sutta_majjhima_mūla"] = sutta_majjhima_mūla
    tipitaka_dict["sutta_majjhima_aṭṭhakathā"] = sutta_majjhima_aṭṭhakathā
    tipitaka_dict["sutta_majjhima_ṭīkā"] = sutta_majjhima_ṭīkā

    # saṃyutta

    sutta_saṃyutta_mūla = ["s0301m.mul.txt", "s0302m.mul.txt", "s0303m.mul.txt", "s0304m.mul.txt", "s0305m.mul.txt"]
    sutta_saṃyutta_aṭṭhakathā = ["s0301a.att.txt", "s0302a.att.txt", "s0303a.att.txt", "s0304a.att.txt", "s0305a.att.txt"]
    sutta_saṃyutta_ṭīkā = ["s0301t.tik.txt", "s0302t.tik.txt", "s0303t.tik.txt", "s0304t.tik.txt", "s0305t.tik.txt"]

    tipitaka_dict["sutta_saṃyutta_mūla"] = sutta_saṃyutta_mūla
    tipitaka_dict["sutta_saṃyutta_aṭṭhakathā"] = sutta_saṃyutta_aṭṭhakathā
    tipitaka_dict["sutta_saṃyutta_ṭīkā"] = sutta_saṃyutta_ṭīkā

    # aṅguttara

    sutta_aṅguttara_mūla = ["s0401m.mul.txt", "s0402m1.mul.txt", "s0402m2.mul.txt", "s0402m3.mul.txt", "s0403m1.mul.txt", "s0403m2.mul.txt", "s0403m3.mul.txt", "s0404m1.mul.txt", "s0404m2.mul.txt", "s0404m3.mul.txt", "s0404m4.mul.txt"]
    sutta_aṅguttara_aṭṭhakathā = ["s0401a.att.txt", "s0402a.att.txt", "s0403a.att.txt", "s0404a.att.txt"]
    sutta_aṅguttara_ṭīkā = ["s0401t.tik.txt", "s0402t.tik.txt", "s0403t.tik.txt", "s0404t.tik.txt"]

    tipitaka_dict["sutta_aṅguttara_mūla"] = sutta_aṅguttara_mūla
    tipitaka_dict["sutta_aṅguttara_aṭṭhakathā"] = sutta_aṅguttara_aṭṭhakathā
    tipitaka_dict["sutta_aṅguttara_ṭīkā"] = sutta_aṅguttara_ṭīkā

    # khuddaka1 - Early wisdom collections:
    # Khuddakapāṭhapāḷi (I include this here, as although the collection is late, the contents are early)
    # Dhammapadapāḷi
    # Udānapāḷi
    # Itivuttakapāḷi
    # Suttanipātapāḷi
    # Theragāthāpāḷi
    # Therīgāthāpāḷi
    # Jātakapāḷi-1
    # Jātakapāḷi-2

    sutta_khuddaka1_mūla = ["s0501m.mul.txt", "s0502m.mul.txt", "s0503m.mul.txt", "s0504m.mul.txt", "s0505m.mul.txt", "s0508m.mul.txt", "s0509m.mul.txt", "s0513m.mul.txt", "s0514m.mul.txt"]

    sutta_khuddaka1_aṭṭhakathā = ["s0501a.att.txt", "s0502a.att.txt", "s0503a.att.txt", "s0504a.att.txt", "s0505a.att.txt", "s0508a1.att.txt", "s0508a2.att.txt", "s0509a.att.txt", "s0513a1.att.txt", "s0513a2.att.txt", "s0513a3.att.txt", "s0513a4.att.txt", "s0514a1.att.txt", "s0514a2.att.txt", "s0514a3.att.txt"]

    tipitaka_dict["sutta_khuddaka1_mūla"] = sutta_khuddaka1_mūla
    tipitaka_dict["sutta_khuddaka1_aṭṭhakathā"] = sutta_khuddaka1_aṭṭhakathā

    # khuddaka2 - Late story collections:
    # Vimānavatthupāḷi
    # Petavatthupāḷi
    # Apadānapāḷi-1
    # Apadānapāḷi-2
    # Buddhavaṃsapāḷi
    # Cariyāpiṭakapāḷi

    sutta_khuddaka2_mūla = ["s0506m.mul.txt", "s0507m.mul.txt", "s0510m1.mul.txt", "s0510m2.mul.txt", "s0511m.mul.txt", "s0512m.mul.txt"]
    sutta_khuddaka2_aṭṭhakathā = ["s0506a.att.txt", "s0507a.att.txt", "s0510a.att.txt", "s0511a.att.txt", "s0512a.att.txt"]

    tipitaka_dict["sutta_khuddaka2_mūla"] = sutta_khuddaka2_mūla
    tipitaka_dict["sutta_khuddaka2_aṭṭhakathā"] = sutta_khuddaka2_aṭṭhakathā

    # khuddaka2- Commentarial/Abhidhammic texts:
    # Mahāniddesapāḷi
    # Cūḷaniddesapāḷi
    # Paṭisambhidāmaggapāḷi
    # Nettippakaraṇapāḷi
    # Milindapañhapāḷi
    # Peṭakopadesapāḷi

    sutta_khuddaka3_mūla = ["s0515m.mul.txt", "s0516m.mul.txt", "s0517m.mul.txt", "s0518m.nrf.txt", "s0519m.mul.txt", "s0520m.nrf.txt"]
    sutta_khuddaka3_aṭṭhakathā = ["s0515a.att.txt", "s0516a.att.txt", "s0517a.att.txt", "s0519a.att.txt"]
    sutta_khuddaka3_ṭīkā = ["s0519t.tik.txt", "s0501t.nrf.txt"]

    tipitaka_dict["sutta_khuddaka3_mūla"] = sutta_khuddaka3_mūla
    tipitaka_dict["sutta_khuddaka3_aṭṭhakathā"] = sutta_khuddaka3_aṭṭhakathā
    tipitaka_dict["sutta_khuddaka3_ṭīkā"] = sutta_khuddaka3_ṭīkā

    # abhidhamma mūla

    abhidhamma_dhammasaṅgaṇī_mūla = ["abh01m.mul.txt"]
    abhidhamma_vibhāṅga_mūla = ["abh02m.mul.txt"]
    abhidhamma_dhātukathā_mūla = ["abh03m1.mul.txt"]
    abhidhamma_puggalapaññatti_mūla = ["abh03m2.mul.txt"]
    abhidhamma_kathāvatthu_mūla = ["abh03m3.mul.txt"]
    abhidhamma_yamaka_mūla = ["abh03m4.mul.txt", "abh03m5.mul.txt", "abh03m6.mul.txt"]
    abhidhamma_paṭṭhāna_mūla = ["abh03m7.mul.txt", "abh03m8.mul.txt", "abh03m9.mul.txt", "abh03m10.mul.txt", "abh03m11.mul.txt"]

    tipitaka_dict["abhidhamma_dhammasaṅgaṇī_mūla"] = abhidhamma_dhammasaṅgaṇī_mūla
    tipitaka_dict["abhidhamma_vibhāṅga_mūla"] = abhidhamma_vibhāṅga_mūla
    tipitaka_dict["abhidhamma_dhātukathā_mūla"] = abhidhamma_dhātukathā_mūla
    tipitaka_dict["abhidhamma_puggalapaññatti_mūla"] = abhidhamma_puggalapaññatti_mūla
    tipitaka_dict["abhidhamma_kathāvatthu_mūla"] = abhidhamma_kathāvatthu_mūla
    tipitaka_dict["abhidhamma_yamaka_mūla"] = abhidhamma_yamaka_mūla
    tipitaka_dict["abhidhamma_paṭṭhāna_mūla"] = abhidhamma_paṭṭhāna_mūla

    # abhidhamma aṭṭhakathā

    abhidhamma_aṭṭhakathā = ["abh01a.att.txt", "abh02a.att.txt", "abh03a.att.txt",]
    tipitaka_dict["abhidhamma_aṭṭhakathā"] = abhidhamma_aṭṭhakathā

    # abhidhamma ṭīkā

    abhidhamma_ṭīkā = [
        "abh01t.tik.txt", "abh02t.tik.txt", "abh03t.tik.txt",
        "abh04t.nrf.txt", "abh05t.nrf.txt", "abh06t.nrf.txt",
        "abh07t.nrf.txt", "abh08t.nrf.txt", "abh09t.nrf.txt"]
    tipitaka_dict["abhidhamma_ṭīkā"] = abhidhamma_ṭīkā

    # aññā
    aññā_visuddhimagga = ["e0101n.mul.txt", "e0102n.mul.txt"]
    aññā_visuddhimagga_ṭīkā = ["e0103n.att.txt", "e0104n.att.txt", "e0105n.nrf.txt"]
    aññā_leḍī = ["e0201n.nrf.txt", "e0301n.nrf.txt", "e0401n.nrf.txt", "e0501n.nrf.txt"]
    aññā_buddha_vandanā = ["e0601n.nrf.txt", "e0602n.nrf.txt", "e0603n.nrf.txt", "e0604n.nrf.txt", "e0605n.nrf.txt", "e0606n.nrf.txt", "e0607n.nrf.txt", "e0608n.nrf.txt"]
    aññā_vaṃsa = ["e0701n.nrf.txt", "e0702n.nrf.txt", "e0703n.nrf.txt"]
    aññā_byākaraṇa = ["e0801n.nrf.txt", "e0802n.nrf.txt", "e0803n.nrf.txt", "e0804n.nrf.txt", "e0805n.nrf.txt", "e0806n.nrf.txt", "e0807n.nrf.txt", "e0808n.nrf.txt", "e0809n.nrf.txt", "e0810n.nrf.txt", "e0811n.nrf.txt", "e0812n.nrf.txt", "e0813n.nrf.txt", "e1211n.nrf.txt", "e1212n.nrf.txt", "e1213n.nrf.txt", "e1214n.nrf.txt"]
    aññā_pucchavisajjana = ["e0901n.nrf.txt", "e0902n.nrf.txt", "e0903n.nrf.txt", "e0904n.nrf.txt", "e0905n.nrf.txt", "e0906n.nrf.txt", "e0907n.nrf.txt"]
    aññā_nīti = ["e1001n.nrf.txt", "e1002n.nrf.txt", "e1003n.nrf.txt", "e1004n.nrf.txt", "e1005n.nrf.txt", "e1006n.nrf.txt", "e1007n.nrf.txt", "e1008n.nrf.txt", "e1009n.nrf.txt", "e1010n.nrf.txt"]
    aññā_pakiṇṇaka = ["e1101n.nrf.txt", "e1102n.nrf.txt", "e1103n.nrf.txt"]
    aññā_sihaḷa = ["e1201n.nrf.txt", "e1202n.nrf.txt", "e1203n.nrf.txt", "e1204n.nrf.txt", "e1205n.nrf.txt", "e1206n.nrf.txt", "e1207n.nrf.txt", "e1208n.nrf.txt", "e1209n.nrf.txt", "e1210n.nrf.txt", "e1215n.nrf.txt"]

    tipitaka_dict["aññā_visuddhimagga"] = aññā_visuddhimagga
    tipitaka_dict["aññā_visuddhimagga_ṭīkā"] = aññā_visuddhimagga_ṭīkā
    tipitaka_dict["aññā_leḍī"] = aññā_leḍī
    tipitaka_dict["aññā_buddha_vandanā"] = aññā_buddha_vandanā
    tipitaka_dict["aññā_vaṃsa"] = aññā_vaṃsa
    tipitaka_dict["aññā_byākaraṇa"] = aññā_byākaraṇa
    tipitaka_dict["aññā_pucchavisajjana"] = aññā_pucchavisajjana
    tipitaka_dict["aññā_nīti"] = aññā_nīti
    tipitaka_dict["aññā_pakiṇṇaka"] = aññā_pakiṇṇaka
    tipitaka_dict["aññā_sihaḷa"] = aññā_sihaḷa

    # master list of sections

    list_of_sections = [
        vinaya_pārājika_mūla,
        vinaya_pārājika_aṭṭhakathā,
        vinaya_ṭīkā,
        vinaya_pācittiya_mūla,
        vinaya_pācittiya_aṭṭhakathā,
        vinaya_mahāvagga_mūla,
        vinaya_mahāvagga_aṭṭhakathā,
        vinaya_cūḷavagga_mūla,
        vinaya_cūḷavagga_aṭṭhakathā,
        vinaya_parivāra_mūla,
        vinaya_parivāra_aṭṭhakathā,
        sutta_dīgha_mūla,
        sutta_dīgha_aṭṭhakathā,
        sutta_dīgha_ṭīkā,
        sutta_majjhima_mūla,
        sutta_majjhima_aṭṭhakathā,
        sutta_majjhima_ṭīkā,
        sutta_saṃyutta_mūla,
        sutta_saṃyutta_aṭṭhakathā,
        sutta_saṃyutta_ṭīkā,
        sutta_aṅguttara_mūla,
        sutta_aṅguttara_aṭṭhakathā,
        sutta_aṅguttara_ṭīkā,
        sutta_khuddaka1_mūla,
        sutta_khuddaka1_aṭṭhakathā,
        sutta_khuddaka2_mūla,
        sutta_khuddaka2_aṭṭhakathā,
        sutta_khuddaka3_mūla,
        sutta_khuddaka3_aṭṭhakathā,
        sutta_khuddaka3_ṭīkā,
        abhidhamma_dhammasaṅgaṇī_mūla,
        abhidhamma_vibhāṅga_mūla,
        abhidhamma_dhātukathā_mūla,
        abhidhamma_puggalapaññatti_mūla,
        abhidhamma_kathāvatthu_mūla,
        abhidhamma_yamaka_mūla,
        abhidhamma_paṭṭhāna_mūla,
        abhidhamma_aṭṭhakathā,
        abhidhamma_ṭīkā,
        aññā_visuddhimagga,
        aññā_visuddhimagga_ṭīkā,
        aññā_leḍī,
        aññā_buddha_vandanā,
        aññā_vaṃsa,
        aññā_byākaraṇa,
        aññā_pucchavisajjana,
        aññā_nīti,
        aññā_pakiṇṇaka,
        aññā_sihaḷa
    ]

    print(len(tipitaka_dict))

    sanity_tests(pth, tipitaka_dict, list_of_sections)


def sanity_tests(pth: ProjectPaths, tipitaka_dict, list_of_sections):
    """Check book counts."""
    # sanity test

    print("[green]sanity tests")
    print(f"tipitaka_dict {len(tipitaka_dict)}")
    print(f"list_of_sections {len(list_of_sections)}")

    all_files = []
    for __root__, __dirs__, files in os.walk(pth.cst_txt_dir, topdown=False):
        for file in files:
            all_files.append(file)

    print(f"all files {len(all_files)}")

    all_files_in_sections = []
    for section in list_of_sections:
        for filez in section:
            all_files_in_sections.append(filez)

    print(f"all files in sections {len(all_files_in_sections)}")

    all_files_in_tipitaka_dict = []
    for values in tipitaka_dict.values():
        for value in values:
            all_files_in_tipitaka_dict.append(value)

    print(f"all files in tipitaka_dict {len(all_files_in_tipitaka_dict)}")

    # difference1 = set(all_files) ^ set(all_files_in_sections)
    # difference2 = set(all_files_in_sections) ^ set(all_files_in_tipitaka_dict)

    # print(f"[bright_red]difference1: {len(difference1)}")
    # print(f"[bright_red]{difference1}")
    # print(f"[bright_red]difference2: {len(difference2)}")
    # print(f"[bright_red]{difference2}")

    make_raw_text_csv(pth, tipitaka_dict)


def make_raw_text_csv(pth: ProjectPaths, tipitaka_dict):
    """Make clean text files, just letters no punctation."""
    print("[green]making raw text csvs")

    full_text = ""
    ebt_text = ""

    for section, texts in tipitaka_dict.items():
        print(f"{section}")

        text_clean = ""

        for t in texts:
            f = open(pth.cst_txt_dir.joinpath(t))
            file_read = f.read()
            text_clean += f"{clean_machine(file_read)}\n\n"

            if t in ebts:
                ebt_text += f"{clean_machine(file_read)}\n\n"

        full_text += text_clean

        with open(
                pth.raw_text_dir.joinpath(section).with_suffix(".txt"),
                "w") as f:
            f.write(text_clean)

        # !!! make one function for all these raw and csv saves
        # !!! text, df, raw_text_path word_count_path

        word_count_df = make_word_count_df(text_clean)
        word_count_df.to_csv(
            pth.word_count_dir.joinpath(section).with_suffix(".csv"),
            sep="\t", index=False, header=False)

    save_ebt_raw_text_and_csv(pth, ebt_text)
    save_tipitaka_raw_text_and_csv(pth, full_text)


def make_word_count_df(text):
    """Tokenize the words and count frequency."""
    words = nltk.word_tokenize(text)
    freq = nltk.FreqDist(words).most_common()
    word_count_df = pd.DataFrame(freq)
    return word_count_df


def save_tipitaka_raw_text_and_csv(pth: ProjectPaths, full_text):
    """Save full tipitaka frequency, all files in one."""
    print("[green]saving tipiṭaka csv")

    with open(pth.tipitaka_raw_text_path, "w") as f:
        f.write(full_text)

    full_text_df = make_word_count_df(full_text)
    full_text_df.to_csv(
        pth.tipitaka_word_count_path,
        sep="\t", index=False, header=False)


def save_ebt_raw_text_and_csv(pth: ProjectPaths, ebt_text):
    """Save Early Buddhist Texts frequency."""
    print("[green]saving ebts csv")

    with open(
            pth.ebt_raw_text_path, "w") as f:
        f.write(ebt_text)

    ebt_text_df = make_word_count_df(ebt_text)
    ebt_text_df.to_csv(
        pth.ebt_word_count_path,
        sep="\t", index=False, header=False)


if __name__ == "__main__":
    main()
