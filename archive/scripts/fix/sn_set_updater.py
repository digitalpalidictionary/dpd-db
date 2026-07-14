#!/usr/bin/env python3

"""
Update set names of Saṃyutta Nikāya suttas from
`suttas of the Saṃyutta Nikāya` >
`suttas of Saṃyutta Nikāya 1`
"""

import re

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def get_sn_book(i: DpdHeadword) -> str:
    # return re.findall(r"\(SN(\d*)\..+?\)", i.meaning_2)
    trim_front = re.sub(r".+\(SN", "", i.meaning_2)
    trim_back = re.sub(r"\..+", "", trim_front)
    return trim_back


def update_set(db_data: list[DpdHeadword]) -> None:
    for i in db_data:
        sn_book = get_sn_book(i)
        i.family_set = f"suttas of Saṃyutta Nikāya {sn_book}"
        print(i.meaning_2)
        print(i.family_set)
        print()


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db_data = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.family_set == "suttas of the Saṃyutta Nikāya")
        .all()
    )
    update_set(db_data)
    db_session.commit()


if __name__ == "__main__":
    main()
