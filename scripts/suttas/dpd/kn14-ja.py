import re
from pathlib import Path

from sqlalchemy import and_, not_

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.sort_naturally import natural_sort

pth: ProjectPaths = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)

# search_string = r"\((ITI\d+\.\d+-*\d*)\)" # with dots n dashes
search_string = r"\((JA\d+)\)"  # no dots or dashes
file_path = Path("scripts/suttas/dpd/kn14-ja.tsv")


def extractor():
    results = (
        db_session.query(DpdHeadword)
        .filter(
            and_(
                DpdHeadword.meaning_2.regexp_match(search_string),
                not_(DpdHeadword.lemma_1.contains("nipāta")),
            )
        )
        .all()
    )
    extract_dict = {}
    for i in results:
        sutta_code = re.findall(search_string, i.meaning_2)[0]

        if sutta_code not in extract_dict:
            extract_dict[sutta_code] = [i.lemma_1]
        else:
            extract_dict[sutta_code] += [i.lemma_1]

    list_of_keys = [k for k in extract_dict]
    file_order = natural_sort(list_of_keys)

    file_path.open("w")

    with open(file_path, "a") as f:
        for i in file_order:
            f.write(f"{i}\t{', '.join(extract_dict[i])}\n")
            print(f"{i}\t{extract_dict[i]}")


if __name__ == "__main__":
    extractor()
