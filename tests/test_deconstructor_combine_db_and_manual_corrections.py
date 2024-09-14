#!/usr/bin/env python3

"""Combine all the sandhi compounds in db with manual corrections,
so that they are all recognised in deconstructor."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadwords

from tools.meaning_construction import clean_construction
from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv

def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadwords).all()
    
    sandhi_dict = {}
    sandhi_dupes = []
    for i in db:
        if i.pos == "sandhi" and i.meaning_1:
            constr_clean = clean_construction(i.construction).strip()
            if i.lemma_clean not in sandhi_dict:
                sandhi_dict[i.lemma_clean] = [constr_clean]
            else:
                if constr_clean not in sandhi_dict[i.lemma_clean]:
                    sandhi_dict[i.lemma_clean] += [constr_clean]
                else:
                    sandhi_dupes += [i.lemma_clean]

    print(len(sandhi_dict))

    manual_data = read_tsv(pth.decon_manual_corrections)
    manual_dict = {}
    manual_dupes = []
    for i in manual_data:
        word, breakup = i
        breakup = breakup.strip()
        if word not in manual_dict:
            manual_dict[word] = [breakup]
        else:
            if breakup not in manual_dict[word]:
                manual_dict[word] += [breakup]
            else:
                manual_dupes += [word]
    print(len(manual_dict))

    new_dict = {}
    new_dupes = []
    for word, breakups in manual_dict.items():
        for breakup in breakups:
            if word not in new_dict:
                new_dict[word] = [breakup]
            else:
                if breakup not in new_dict[word]:
                    new_dict[word] += [breakup]                      
                else:
                    new_dupes += [word]

    for word, breakups in sandhi_dict.items():
        for breakup in breakups:
            if word not in new_dict:
                new_dict[word] = [breakup]
            else:
                if breakup not in new_dict[word]:
                    new_dict[word] += [breakup]                      
                else:
                    new_dupes += [word]

    print(len(new_dict))

    with open(pth.decon_manual_corrections, "w") as file:
        for word, breakups in new_dict.items():
            for breakup in breakups:
                file.write(f"{word}\t{breakup}\n")

if __name__ == "__main__":
    main()
