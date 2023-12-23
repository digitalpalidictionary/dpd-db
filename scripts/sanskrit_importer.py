#!/usr/bin/env python3

"""Import Ram's Sanskrit additions."""

from rich import print
import pandas as pd

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(PaliWord).all()

    df = pd.read_excel("/home/bodhirasa/Downloads/DPD Sanskrit Updates v1.xlsx")
    print(df.columns)
    # 'id', 'pali_1', 'pali_2', 'sanskrit', 'sanskrit2'
    for index, sk in df.iterrows():
        i = db_session.query(PaliWord).filter(PaliWord.id == sk.id).one()
        print(f"[white]{i.pali_1}")
        print(f"[green]{i.sanskrit}")
        print(f"[cyan]{sk.sanskrit2}")
        input()








if __name__ == "__main__":
    main()
