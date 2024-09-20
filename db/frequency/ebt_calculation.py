#!/usr/bin/env python3

"""Create frequency for collection of EBT suttas and Vinaya mūla and save into database."""

import pandas as pd
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths


def make_dicts(pth: ProjectPaths):
    print("[green]making word count dict of ebt with vinaya ")

    wc_dir = pth.word_count_dir

    vinaya_pārājika_mūla = pd.read_csv(wc_dir.joinpath("vinaya_pārājika_mūla.csv"), sep="\t", header=None)
    vinaya_pācittiya_mūla = pd.read_csv(wc_dir.joinpath("vinaya_pācittiya_mūla.csv"), sep="\t", header=None)
    vinaya_mahāvagga_mūla = pd.read_csv(wc_dir.joinpath("vinaya_mahāvagga_mūla.csv"), sep="\t", header=None)
    vinaya_cūḷavagga_mūla = pd.read_csv(wc_dir.joinpath("vinaya_cūḷavagga_mūla.csv"), sep="\t", header=None)
    vinaya_parivāra_mūla = pd.read_csv(wc_dir.joinpath("vinaya_parivāra_mūla.csv"), sep="\t", header=None)
    sutta_dīgha_mūla = pd.read_csv(wc_dir.joinpath("sutta_dīgha_mūla.csv"), sep="\t", header=None)
    sutta_majjhima_mūla = pd.read_csv(wc_dir.joinpath("sutta_majjhima_mūla.csv"), sep="\t", header=None)
    sutta_saṃyutta_mūla = pd.read_csv(wc_dir.joinpath("sutta_saṃyutta_mūla.csv"), sep="\t", header=None)
    sutta_aṅguttara_mūla = pd.read_csv(wc_dir.joinpath("sutta_aṅguttara_mūla.csv"), sep="\t", header=None)
    sutta_khuddaka1_mūla = pd.read_csv(wc_dir.joinpath("sutta_khuddaka1_mūla.csv"), sep="\t", header=None)

    vinaya_pārājika_mūla_dict = dict(vinaya_pārājika_mūla.values.tolist())
    vinaya_pācittiya_mūla_dict = dict(vinaya_pācittiya_mūla.values.tolist())
    vinaya_mahāvagga_mūla_dict = dict(vinaya_mahāvagga_mūla.values.tolist())
    vinaya_cūḷavagga_mūla_dict = dict(vinaya_cūḷavagga_mūla.values.tolist())
    vinaya_parivāra_mūla_dict = dict(vinaya_parivāra_mūla.values.tolist())
    sutta_dīgha_mūla_dict = dict(sutta_dīgha_mūla.values.tolist())
    sutta_majjhima_mūla_dict = dict(sutta_majjhima_mūla.values.tolist())
    sutta_saṃyutta_mūla_dict = dict(sutta_saṃyutta_mūla.values.tolist())
    sutta_aṅguttara_mūla_dict = dict(sutta_aṅguttara_mūla.values.tolist())
    sutta_khuddaka1_mūla_dict = dict(sutta_khuddaka1_mūla.values.tolist())

    dicts = [
        vinaya_pārājika_mūla_dict,
        vinaya_pācittiya_mūla_dict,
        vinaya_mahāvagga_mūla_dict,
        vinaya_cūḷavagga_mūla_dict,
        vinaya_parivāra_mūla_dict,
        sutta_dīgha_mūla_dict,
        sutta_majjhima_mūla_dict,
        sutta_saṃyutta_mūla_dict,
        sutta_aṅguttara_mūla_dict,
        sutta_khuddaka1_mūla_dict,
    ]
    return dicts


def calculate_ebt_count():
    tic()
    print("[bright_yellow]EBT & Vinaya mūla frequency calculation")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    dpd_db = db_session.query(DpdHeadword).all()

    dicts = make_dicts(pth)

    # Create a list to store counts for each dictionary
    dictionary_counts = [{} for _ in dicts]

    for __counter__, i in enumerate(dpd_db):
        
        inflections = i.inflections_list

        for idx, dictionary in enumerate(dicts):
            count: int = 0
            for inflection in inflections:
                if inflection in dictionary:
                    count += int(dictionary.get(inflection, 0))

            # Store the count for this word in the corresponding dictionary's counts
            dictionary_counts[idx][i.lemma_1] = count

    # Calculate and print the total counts for all words
    total_word_counts = {}
    for word in dpd_db:
        total_count = sum(dictionary_counts[idx].get(word.lemma_1, 0) for idx in range(len(dicts)))
        total_word_counts[word.lemma_1] = total_count

        word.ebt_count = total_count

    # print("\nTotal Counts:")
    # for word, total_count in total_word_counts.items():
    #     print(f"{word}: {total_count}")

    db_session.commit()

    db_session.close()

    toc()


if __name__ == "__main__":
    calculate_ebt_count()
