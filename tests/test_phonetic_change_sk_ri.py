#!/usr/bin/env python3

"""Find phonetic changes because of Sanskrit ṛ"""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    
    results = db_session \
        .query(DpdHeadword) \
        .all()
    
    reduced_results = []
    for r in results:
        if r.root_key:
            if (
                "ṛ" in r.rt.sanskrit_root
                and ">" in r.phonetic
                and r.meaning_1
            ):
                reduced_results.append(r)
    
    length = len(reduced_results)
    start_point = 448

    for index, r in enumerate(reduced_results):
        if index > start_point:
            print(f"[green]{index+1} / {length+1}")
            print(f"[green]{'headword':40}[white]{r.lemma_1}")
            
            phonetic_split = r.phonetic.split("\n")
            if len(phonetic_split) == 1:
                print(f"[green]{'phonetic':<40}[yellow]{phonetic_split[0]}")
            else:
                for ph_index, ph in enumerate(phonetic_split):
                    if ph_index == 0:
                        print(f"[green]{'phonetic':<40}[yellow]- {ph}")
                    else:
                        print(f"[green]{'':<40}[yellow]- {ph}")

            print(f"[green]{'sk root':<40}[white]{r.rt.sanskrit_root}")
            print(f"[green]{'sanskrit':<40}[white]{r.sanskrit}")
            input()


if __name__ == "__main__":
    main()

    # a > i (kicca, adhicca 1.1)
    # a > u (akukkuca, ativuṭṭha, avāpuraṇa)
    # ana > aṇa (karaNa)
    # ar > ubb (anukubbati)
    # cos of sk ṛ
    # dd > ṭṭ (aṭṭa 1.1, aṭṭita, aṭṭiyati)
    # i > ā (avakāraka)
    # jjt > ṭṭh (anissaṭṭha)
    # k > kh (anabhisaṅkharitvā)
    # rn > ṇṇ (aṇṇava, tiṇṇa)
    # rt > ṭ (kaṭa)
    # rth > ṭṭh (aṭṭha 2.1)
    # sar > s (atisitvā)
    # st > ṭṭh (accukkaṭṭha, ativuṭṭha)
    # uj > ajj (ajjava)
    # ṭ > t (anuvattana)
    # ṛ > ar (sabbathā)
    # hāriya > hira (asaṃhira)
    # 


    # ignore
    # a > ā