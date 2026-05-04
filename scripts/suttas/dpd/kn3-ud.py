import re
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.sort_naturally import natural_sort

pth: ProjectPaths = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def ud_extractor():
    # search_string = r"\((UD\d+\.\d+-*\d*)\)" # with dots n dashes
    search_string = r"\((UD\d+)\)"  # no dots or dashes
    results = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.meaning_2.regexp_match(search_string))
        .all()
    )
    an_dict = {}
    for i in results:
        sutta_code = re.findall(search_string, i.meaning_2)[0]

        if sutta_code not in an_dict:
            an_dict[sutta_code] = [i.lemma_1]
        else:
            an_dict[sutta_code] += [i.lemma_1]

    list_of_keys = [k for k in an_dict]
    file_order = natural_sort(list_of_keys)

    file_path = Path("scripts/suttas/dpd/kn3-ud.tsv")
    file_path.open("w")

    with open(file_path, "a") as f:
        for i in file_order:
            f.write(f"{i}\t{', '.join(an_dict[i])}\n")
            print(f"{i}\t{an_dict[i]}")


if __name__ == "__main__":
    ud_extractor()
