#!/usr/bin/env python3
import csv

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths as PTH


def main():
    print("[bright_yellow]copying dps meaning_1 to meaning_2")
    db_session = get_db_session(PTH.dpd_db_path)
    dpd_db = db_session.query(PaliWord).all()

    dict = {}
    with open(
        PTH.dps_merge_dir.joinpath(
                "meaning_1").with_suffix(".csv")) as f:
        reader = csv.DictReader(f, delimiter=",")
        for r in reader:
            text_string = f"{r['meaning_1']}"
            if r['meaning_lit']:
                text_string += f"; lit. {r['meaning_lit']}"
                # print(f"[green]{r['pali_1']:<30} [blue]{text_string}")
            dict[int(r["id"])] = text_string

    print(len(dict))
    changed = 0
    for counter, i in enumerate(dpd_db):

        if i.user_id in dict:
            i.meaning_1 = ""
            i.meaning_2 = dict[i.user_id]
            # print(f"[green]{i.pali_1:<30}[blue]{i.pos:<10}[cyan]{i.meaning_2}")
            changed += 1

    print(changed)
    db_session.commit()


if __name__ == "__main__":
    main()
