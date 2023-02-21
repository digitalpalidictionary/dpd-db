
import nltk
import pandas as pd
import os

from rich import print
from helpers import get_paths
from tools.clean_machine import clean_machine
from tools.pali_text_files import ebts
# nltk.download('punkt')


def main():
    print("[bright_yellow]generating text lists")
    global pth
    pth = get_paths()
    make_tipitaka_dict()


def make_tipitaka_dict():
    print("[green]making master dict", end=" ")
    tipitaka_dict = {}

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!! is it possible !!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # !!!!!!!!!!!!!!!!!!!!!!!!! to combine this with !!!!!!!!!!!!!!!!!!!!!!
    # !!!!!!!!!!!!!!!!! the list of text for sandhi splitting? !!!!!!!!!!!!!

    # vinaya

    vinaya_pārājika_mūla = ["vin01m.mul.xml.txt"]
    vinaya_pārājika_aṭṭhakathā = ["vin01a.att.xml.txt"]
    vinaya_ṭīkā = ["vin01t1.tik.xml.txt", "vin01t2.tik.xml.txt", "vin02t.tik.xml.txt", "vin04t.nrf.xml.txt", "vin05t.nrf.xml.txt", "vin06t.nrf.xml.txt", "vin07t.nrf.xml.txt", "vin08t.nrf.xml.txt", "vin09t.nrf.xml.txt", "vin10t.nrf.xml.txt", "vin11t.nrf.xml.txt", "vin12t.nrf.xml.txt", "vin13t.nrf.xml.txt"]

    tipitaka_dict["vinaya_pārājika_mūla"] = vinaya_pārājika_mūla
    tipitaka_dict["vinaya_pārājika_aṭṭhakathā"] = vinaya_pārājika_aṭṭhakathā
    tipitaka_dict["vinaya_ṭīkā"] = vinaya_ṭīkā

    vinaya_pācittiya_mūla = ["vin02m1.mul.xml.txt"]
    vinaya_pācittiya_aṭṭhakathā = ["vin02a1.att.xml.txt"]

    tipitaka_dict["vinaya_pācittiya_mūla"] = vinaya_pācittiya_mūla
    tipitaka_dict["vinaya_pācittiya_aṭṭhakathā"] = vinaya_pācittiya_aṭṭhakathā

    vinaya_mahāvagga_mūla = ["vin02m2.mul.xml.txt"]
    vinaya_mahāvagga_aṭṭhakathā = ["vin02a2.att.xml.txt"]

    tipitaka_dict["vinaya_mahāvagga_mūla"] = vinaya_mahāvagga_mūla
    tipitaka_dict["vinaya_mahāvagga_aṭṭhakathā"] = vinaya_mahāvagga_aṭṭhakathā

    vinaya_cūḷavagga_mūla = ["vin02m3.mul.xml.txt"]
    vinaya_cūḷavagga_aṭṭhakathā = ["vin02a3.att.xml.txt"]

    tipitaka_dict["vinaya_cūḷavagga_mūla"] = vinaya_cūḷavagga_mūla
    tipitaka_dict["vinaya_cūḷavagga_aṭṭhakathā"] = vinaya_cūḷavagga_aṭṭhakathā

    vinaya_parivāra_mūla = ["vin02m4.mul.xml.txt"]
    vinaya_parivāra_aṭṭhakathā = ["vin02a4.att.xml.txt"]

    tipitaka_dict["vinaya_parivāra_mūla"] = vinaya_parivāra_mūla
    tipitaka_dict["vinaya_parivāra_aṭṭhakathā"] = vinaya_parivāra_aṭṭhakathā

    # sutta

    # dīgha

    sutta_dīgha_mūla = ["s0101m.mul.xml.txt", "s0102m.mul.xml.txt", "s0103m.mul.xml.txt"]
    sutta_dīgha_aṭṭhakathā = ["s0101a.att.xml.txt", "s0102a.att.xml.txt", "s0103a.att.xml.txt"]
    sutta_dīgha_ṭīkā = ["s0101t.tik.xml.txt", "s0102t.tik.xml.txt", "s0103t.tik.xml.txt", "s0104t.nrf.xml.txt", "s0105t.nrf.xml.txt"]

    tipitaka_dict["sutta_dīgha_mūla"] = sutta_dīgha_mūla
    tipitaka_dict["sutta_dīgha_aṭṭhakathā"] = sutta_dīgha_aṭṭhakathā
    tipitaka_dict["sutta_dīgha_ṭīkā"] = sutta_dīgha_ṭīkā

    # majjhima

    sutta_majjhima_mūla = ["s0201m.mul.xml.txt", "s0202m.mul.xml.txt", "s0203m.mul.xml.txt"]
    sutta_majjhima_aṭṭhakathā = ["s0201a.att.xml.txt", "s0202a.att.xml.txt", "s0203a.att.xml.txt"]
    sutta_majjhima_ṭīkā = ["s0201t.tik.xml.txt", "s0202t.tik.xml.txt", "s0203t.tik.xml.txt"]

    tipitaka_dict["sutta_majjhima_mūla"] = sutta_majjhima_mūla
    tipitaka_dict["sutta_majjhima_aṭṭhakathā"] = sutta_majjhima_aṭṭhakathā
    tipitaka_dict["sutta_majjhima_ṭīkā"] = sutta_majjhima_ṭīkā

    # saṃyutta

    sutta_saṃyutta_mūla = ["s0301m.mul.xml.txt", "s0302m.mul.xml.txt", "s0303m.mul.xml.txt", "s0304m.mul.xml.txt", "s0305m.mul.xml.txt"]
    sutta_saṃyutta_aṭṭhakathā = ["s0301a.att.xml.txt", "s0302a.att.xml.txt", "s0303a.att.xml.txt", "s0304a.att.xml.txt", "s0305a.att.xml.txt"]
    sutta_saṃyutta_ṭīkā = ["s0301t.tik.xml.txt", "s0302t.tik.xml.txt", "s0303t.tik.xml.txt", "s0304t.tik.xml.txt", "s0305t.tik.xml.txt"]

    tipitaka_dict["sutta_saṃyutta_mūla"] = sutta_saṃyutta_mūla
    tipitaka_dict["sutta_saṃyutta_aṭṭhakathā"] = sutta_saṃyutta_aṭṭhakathā
    tipitaka_dict["sutta_saṃyutta_ṭīkā"] = sutta_saṃyutta_ṭīkā

    # aṅguttara

    sutta_aṅguttara_mūla = ["s0401m.mul.xml.txt", "s0402m1.mul.xml.txt", "s0402m2.mul.xml.txt", "s0402m3.mul.xml.txt", "s0403m1.mul.xml.txt", "s0403m2.mul.xml.txt", "s0403m3.mul.xml.txt", "s0404m1.mul.xml.txt", "s0404m2.mul.xml.txt", "s0404m3.mul.xml.txt", "s0404m4.mul.xml.txt"]
    sutta_aṅguttara_aṭṭhakathā = ["s0401a.att.xml.txt", "s0402a.att.xml.txt", "s0403a.att.xml.txt", "s0404a.att.xml.txt"]
    sutta_aṅguttara_ṭīkā = ["s0401t.tik.xml.txt", "s0402t.tik.xml.txt", "s0403t.tik.xml.txt", "s0404t.tik.xml.txt"]

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

    sutta_khuddaka1_mūla = ["s0501m.mul.xml.txt", "s0502m.mul.xml.txt", "s0503m.mul.xml.txt", "s0504m.mul.xml.txt", "s0505m.mul.xml.txt", "s0508m.mul.xml.txt", "s0509m.mul.xml.txt", "s0513m.mul.xml.txt", "s0514m.mul.xml.txt"]

    sutta_khuddaka1_aṭṭhakathā = ["s0501a.att.xml.txt", "s0502a.att.xml.txt", "s0503a.att.xml.txt", "s0504a.att.xml.txt", "s0505a.att.xml.txt", "s0508a1.att.xml.txt", "s0508a2.att.xml.txt", "s0509a.att.xml.txt", "s0513a1.att.xml.txt", "s0513a2.att.xml.txt", "s0513a3.att.xml.txt", "s0513a4.att.xml.txt", "s0514a1.att.xml.txt", "s0514a2.att.xml.txt", "s0514a3.att.xml.txt"]

    tipitaka_dict["sutta_khuddaka1_mūla"] = sutta_khuddaka1_mūla
    tipitaka_dict["sutta_khuddaka1_aṭṭhakathā"] = sutta_khuddaka1_aṭṭhakathā

    # khuddaka2 - Late story collections:
    # Vimānavatthupāḷi
    # Petavatthupāḷi
    # Apadānapāḷi-1
    # Apadānapāḷi-2
    # Buddhavaṃsapāḷi
    # Cariyāpiṭakapāḷi

    sutta_khuddaka2_mūla = ["s0506m.mul.xml.txt", "s0507m.mul.xml.txt", "s0510m1.mul.xml.txt", "s0510m2.mul.xml.txt", "s0511m.mul.xml.txt", "s0512m.mul.xml.txt"]
    sutta_khuddaka2_aṭṭhakathā = ["s0506a.att.xml.txt", "s0507a.att.xml.txt", "s0510a.att.xml.txt", "s0511a.att.xml.txt", "s0512a.att.xml.txt"]

    tipitaka_dict["sutta_khuddaka2_mūla"] = sutta_khuddaka2_mūla
    tipitaka_dict["sutta_khuddaka2_aṭṭhakathā"] = sutta_khuddaka2_aṭṭhakathā

    # khuddaka2- Commentarial/Abhidhammic texts:
    # Mahāniddesapāḷi
    # Cūḷaniddesapāḷi
    # Paṭisambhidāmaggapāḷi
    # Nettippakaraṇapāḷi
    # Milindapañhapāḷi
    # Peṭakopadesapāḷi

    sutta_khuddaka3_mūla = ["s0515m.mul.xml.txt", "s0516m.mul.xml.txt", "s0517m.mul.xml.txt", "s0518m.nrf.xml.txt", "s0519m.mul.xml.txt", "s0520m.nrf.xml.txt"]
    sutta_khuddaka3_aṭṭhakathā = ["s0515a.att.xml.txt", "s0516a.att.xml.txt", "s0517a.att.xml.txt", "s0519a.att.xml.txt"]
    sutta_khuddaka3_ṭīkā = ["s0519t.tik.xml.txt", "s0501t.nrf.xml.txt"]

    tipitaka_dict["sutta_khuddaka3_mūla"] = sutta_khuddaka3_mūla
    tipitaka_dict["sutta_khuddaka3_aṭṭhakathā"] = sutta_khuddaka3_aṭṭhakathā
    tipitaka_dict["sutta_khuddaka3_ṭīkā"] = sutta_khuddaka3_ṭīkā

    # abhidhamma

    abhidhamma_dhammasaṅgaṇī_mūla = ["abh01m.mul.xml.txt"]
    abhidhamma_dhammasaṅgaṇī_aṭṭhakathā = ["abh01a.att.xml.txt"]
    abhidhamma_dhammasaṅgaṇī_ṭīkā = ["abh01t.tik.xml.txt", "abh04t.nrf.xml.txt"]

    tipitaka_dict["abhidhamma_dhammasaṅgaṇī_mūla"] = abhidhamma_dhammasaṅgaṇī_mūla
    tipitaka_dict["abhidhamma_dhammasaṅgaṇī_aṭṭhakathā"] = abhidhamma_dhammasaṅgaṇī_aṭṭhakathā
    tipitaka_dict["abhidhamma_dhammasaṅgaṇī_ṭīkā"] = abhidhamma_dhammasaṅgaṇī_ṭīkā

    abhidhamma_vibhāṅga_mūla = ["abh02m.mul.xml.txt"]
    abhidhamma_vibhāṅga_aṭṭhakathā = ["abh02a.att.xml.txt"]
    abhidhamma_vibhāṅga_ṭīkā = ["abh02t.tik.xml.txt"]

    tipitaka_dict["abhidhamma_vibhāṅga_mūla"] = abhidhamma_vibhāṅga_mūla
    tipitaka_dict["abhidhamma_vibhāṅga_aṭṭhakathā"] = abhidhamma_vibhāṅga_aṭṭhakathā
    tipitaka_dict["abhidhamma_vibhāṅga_ṭīkā"] = abhidhamma_vibhāṅga_ṭīkā

    abhidhamma_dhātukathā_mūla = ["abh03m1.mul.xml.txt"]
    abhidhamma_dhātukathā_aṭṭhakathā = ["abh03a1.att.xml.txt"]
    abhidhamma_dhātukathā_ṭīkā = ["abh03t1.tik.xml.txt", "abh05t1.nrf.xml.txt"]

    tipitaka_dict["abhidhamma_dhātukathā_mūla"] = abhidhamma_dhātukathā_mūla
    tipitaka_dict["abhidhamma_dhātukathā_aṭṭhakathā"] = abhidhamma_dhātukathā_aṭṭhakathā
    tipitaka_dict["abhidhamma_dhātukathā_ṭīkā"] = abhidhamma_dhātukathā_ṭīkā

    abhidhamma_puggalapaññatti_mūla = ["abh03m2.mul.xml.txt"]
    abhidhamma_puggalapaññatti_aṭṭhakathā = ["abh03a2.att.xml.txt"]
    abhidhamma_puggalapaññatti_ṭīkā = ["abh03t2.tik.xml.txt", "abh05t2.nrf.xml.txt"]

    tipitaka_dict["abhidhamma_puggalapaññatti_mūla"] = abhidhamma_puggalapaññatti_mūla
    tipitaka_dict["abhidhamma_puggalapaññatti_aṭṭhakathā"] = abhidhamma_puggalapaññatti_aṭṭhakathā
    tipitaka_dict["abhidhamma_puggalapaññatti_ṭīkā"] = abhidhamma_puggalapaññatti_ṭīkā

    abhidhamma_kathāvatthu_mūla = ["abh03m3.mul.xml.txt"]
    abhidhamma_kathāvatthu_aṭṭhakathā = ["abh03a3.att.xml.txt"]
    abhidhamma_kathāvatthu_ṭīkā = ["abh03t3.tik.xml.txt", "abh05t3.nrf.xml.txt"]

    tipitaka_dict["abhidhamma_kathāvatthu_mūla"] = abhidhamma_kathāvatthu_mūla
    tipitaka_dict["abhidhamma_kathāvatthu_aṭṭhakathā"] = abhidhamma_kathāvatthu_aṭṭhakathā
    tipitaka_dict["abhidhamma_kathāvatthu_ṭīkā"] = abhidhamma_kathāvatthu_ṭīkā

    abhidhamma_yamaka_mūla = ["abh03m4.mul.xml.txt", "abh03m5.mul.xml.txt", "abh03m6.mul.xml.txt"]
    abhidhamma_yamaka_aṭṭhakathā = ["abh03a4.att.xml.txt"]
    abhidhamma_yamaka_ṭīkā = ["abh03t4.tik.xml.txt", "abh05t4.nrf.xml.txt"]

    tipitaka_dict["abhidhamma_yamaka_mūla"] = abhidhamma_yamaka_mūla
    tipitaka_dict["abhidhamma_yamaka_aṭṭhakathā"] = abhidhamma_yamaka_aṭṭhakathā
    tipitaka_dict["abhidhamma_yamaka_ṭīkā"] = abhidhamma_yamaka_ṭīkā

    abhidhamma_paṭṭhāna_mūla = ["abh03m7.mul.xml.txt", "abh03m8.mul.xml.txt", "abh03m9.mul.xml.txt", "abh03m10.mul.xml.txt", "abh03m11.mul.xml.txt"]
    abhidhamma_paṭṭhāna_aṭṭhakathā = ["abh03a5.att.xml.txt"]
    abhidhamma_paṭṭhāna_ṭīkā = ["abh03t5.tik.xml.txt", "abh05t5.nrf.xml.txt"]

    tipitaka_dict["abhidhamma_paṭṭhāna_mūla"] = abhidhamma_paṭṭhāna_mūla
    tipitaka_dict["abhidhamma_paṭṭhāna_aṭṭhakathā"] = abhidhamma_paṭṭhāna_aṭṭhakathā
    tipitaka_dict["abhidhamma_paṭṭhāna_ṭīkā"] = abhidhamma_paṭṭhāna_ṭīkā

    abhidhamma_aññā_ṭīkā = ["abh06t.nrf.xml.txt", "abh07t.nrf.xml.txt", "abh08t.nrf.xml.txt", "abh09t.nrf.xml.txt"]

    tipitaka_dict["abhidhamma_aññā_ṭīkā"] = abhidhamma_aññā_ṭīkā

    # aññā

    aññā_visuddhimagga = ["e0101n.mul.xml.txt", "e0102n.mul.xml.txt"]
    aññā_visuddhimagga_ṭīkā = ["e0103n.att.xml.txt", "e0104n.att.xml.txt", "e0105n.nrf.xml.txt"]
    aññā_leḍī = ["e0201n.nrf.xml.txt", "e0301n.nrf.xml.txt", "e0401n.nrf.xml.txt", "e0501n.nrf.xml.txt"]
    aññā_buddha_vandanā = ["e0601n.nrf.xml.txt", "e0602n.nrf.xml.txt", "e0603n.nrf.xml.txt", "e0604n.nrf.xml.txt", "e0605n.nrf.xml.txt", "e0606n.nrf.xml.txt", "e0607n.nrf.xml.txt", "e0608n.nrf.xml.txt"]
    aññā_vaṃsa = ["e0701n.nrf.xml.txt", "e0702n.nrf.xml.txt", "e0703n.nrf.xml.txt"]
    aññā_byākaraṇa = ["e0801n.nrf.xml.txt", "e0802n.nrf.xml.txt", "e0803n.nrf.xml.txt", "e0804n.nrf.xml.txt", "e0805n.nrf.xml.txt", "e0806n.nrf.xml.txt", "e0807n.nrf.xml.txt", "e0808n.nrf.xml.txt", "e0809n.nrf.xml.txt", "e0810n.nrf.xml.txt", "e0811n.nrf.xml.txt", "e0812n.nrf.xml.txt", "e0813n.nrf.xml.txt", "e1211n.nrf.xml.txt", "e1212n.nrf.xml.txt", "e1213n.nrf.xml.txt", "e1214n.nrf.xml.txt"]
    aññā_pucchavisajjana = ["e0901n.nrf.xml.txt", "e0902n.nrf.xml.txt", "e0903n.nrf.xml.txt", "e0904n.nrf.xml.txt", "e0905n.nrf.xml.txt", "e0906n.nrf.xml.txt", "e0907n.nrf.xml.txt"]
    aññā_nīti = ["e1001n.nrf.xml.txt", "e1002n.nrf.xml.txt", "e1003n.nrf.xml.txt", "e1004n.nrf.xml.txt", "e1005n.nrf.xml.txt", "e1006n.nrf.xml.txt", "e1007n.nrf.xml.txt", "e1008n.nrf.xml.txt", "e1009n.nrf.xml.txt", "e1010n.nrf.xml.txt"]
    aññā_pakiṇṇaka = ["e1101n.nrf.xml.txt", "e1102n.nrf.xml.txt", "e1103n.nrf.xml.txt"]
    aññā_sihaḷa = ["e1201n.nrf.xml.txt", "e1202n.nrf.xml.txt", "e1203n.nrf.xml.txt", "e1204n.nrf.xml.txt", "e1205n.nrf.xml.txt", "e1206n.nrf.xml.txt", "e1207n.nrf.xml.txt", "e1208n.nrf.xml.txt", "e1209n.nrf.xml.txt", "e1210n.nrf.xml.txt", "e1215n.nrf.xml.txt"]

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
        abhidhamma_dhammasaṅgaṇī_aṭṭhakathā,
        abhidhamma_dhammasaṅgaṇī_ṭīkā,
        abhidhamma_vibhāṅga_mūla,
        abhidhamma_vibhāṅga_aṭṭhakathā,
        abhidhamma_vibhāṅga_ṭīkā,
        abhidhamma_dhātukathā_mūla,
        abhidhamma_dhātukathā_aṭṭhakathā,
        abhidhamma_dhātukathā_ṭīkā,
        abhidhamma_puggalapaññatti_mūla,
        abhidhamma_puggalapaññatti_aṭṭhakathā,
        abhidhamma_puggalapaññatti_ṭīkā,
        abhidhamma_kathāvatthu_mūla,
        abhidhamma_kathāvatthu_aṭṭhakathā,
        abhidhamma_kathāvatthu_ṭīkā,
        abhidhamma_yamaka_mūla,
        abhidhamma_yamaka_aṭṭhakathā,
        abhidhamma_yamaka_ṭīkā,
        abhidhamma_paṭṭhāna_mūla,
        abhidhamma_paṭṭhāna_aṭṭhakathā,
        abhidhamma_paṭṭhāna_ṭīkā,
        abhidhamma_aññā_ṭīkā,
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

    sanity_tests(tipitaka_dict, list_of_sections)


def sanity_tests(tipitaka_dict, list_of_sections):

    # sanity test

    print("[green]sanity tests")
    print(f"    tipitaka_dict {len(tipitaka_dict)}")
    print(f"    list_of_sections {len(list_of_sections)}")

    # these files have been manually created
    # abh03t1.tik.xml.txt, abh03t2.tik.xml.txt, abh03t3.tik.xml.txt, abh03t4.tik.xml.txt, abh03t5.tik.xml.txt
    # to replace
    # abh03a.att.xml.txt

    # abh05t5.nrf.xml.txt, abh05t4.nrf.xml.txt, abh05t3.nrf.xml.txt, abh05t2.nrf.xml.txt, abh05t1.nrf.xml.txt
    # to replace
    # abh05t.nrf.xml.txt

    # abh03a1.att.xml.txt, abh03a2.att.xml.txt, abh03a3.att.xml.txt, abh03a4.att.xml.txt, abh03a5.att.xml.txt
    # to replace ...
    # abh03t.tik.xml.txt

    all_files = []
    for root, dirs, files in os.walk(pth.cst_txt_dir, topdown=False):
        for file in files:
            all_files.append(file)

    print(f"    all files {len(all_files)}")

    all_files_in_sections = []
    for section in list_of_sections:
        for filez in section:
            all_files_in_sections.append(filez)

    print(f"    all files in sections {len(all_files_in_sections)}")

    all_files_in_tipitaka_dict = []
    for values in tipitaka_dict.values():
        for value in values:
            all_files_in_tipitaka_dict.append(value)

    print(f"    all files in tipitaka_dict {len(all_files_in_tipitaka_dict)}")

    # difference1 = set(all_files) ^ set(all_files_in_sections)
    # difference2 = set(all_files_in_sections) ^ set(all_files_in_tipitaka_dict)

    # print(f"    [bright_red]difference1: {len(difference1)}")
    # print(f"    [bright_red]{difference1}")
    # print(f"    [bright_red]difference2: {len(difference2)}")
    # print(f"    [bright_red]{difference2}")

    make_raw_text_csv(tipitaka_dict)


def make_raw_text_csv(tipitaka_dict):

    print("[green]making raw text csvs")

    full_text = ""
    ebt_text = ""

    for section, texts in tipitaka_dict.items():
        print(f"    {section}")

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

        # !!!!!! make one function for all these raw and csv saves !!!!!!!!
        # !!!!!!!!!!!!!! text, df, raw_text_path word_count_path !!!!!!!!!!!!!!!!

        word_count_df = make_word_count_df(text_clean)
        word_count_df.to_csv(
            pth.word_count_dir.joinpath(section).with_suffix(".csv"),
            sep="\t", index=None, header=None)

    save_ebt_raw_text_and_csv(ebt_text)
    save_tipitaka_raw_text_and_csv(full_text)


def make_word_count_df(text):

    words = nltk.word_tokenize(text)
    freq = nltk.FreqDist(words).most_common()
    word_count_df = pd.DataFrame(freq)
    return word_count_df


def save_tipitaka_raw_text_and_csv(full_text):
    print("[green]saving tipiṭaka csvs")

    with open(pth.tipitaka_raw_text_path, "w") as f:
        f.write(full_text)

    full_text_df = make_word_count_df(full_text)
    full_text_df.to_csv(
        pth.tipitaka_word_count_path,
        sep="\t", index=None, header=None)


def save_ebt_raw_text_and_csv(ebt_text):
    print("[green]saving ebts csvs")

    with open(
            pth.ebt_raw_text_path, "w") as f:
        f.write(ebt_text)

    ebt_text_df = make_word_count_df(ebt_text)
    ebt_text_df.to_csv(
        pth.ebt_word_count_path,
        sep="\t", index=None, header=None)


if __name__ == "__main__":
    main()
