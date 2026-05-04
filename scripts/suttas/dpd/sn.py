import re
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.sort_naturally import natural_sort

pth: ProjectPaths = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def sn_extractor():
    # with open(file_path, "a") as f:
    search_string = r"\((SN\d+\.\d+-*\d*)\)"
    results = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.meaning_2.regexp_match(search_string))
        .all()
    )
    sn_dict = {}
    for i in results:
        sutta_code = re.findall(search_string, i.meaning_2)[0]

        if sutta_code not in sn_dict:
            sn_dict[sutta_code] = [i.lemma_1]
        else:
            sn_dict[sutta_code] += [i.lemma_1]

    list_of_keys = [k for k in sn_dict]
    file_order = natural_sort(list_of_keys)

    file_path = Path("scripts/suttas/dpd/sn.tsv")
    file_path.open("w")

    with open(file_path, "a") as f:
        for i in file_order:
            f.write(f"{i}\t{', '.join(sn_dict[i])}\n")
            print(f"{i}\t{sn_dict[i]}")


if __name__ == "__main__":
    sn_extractor()
