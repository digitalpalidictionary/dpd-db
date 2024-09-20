#!/usr/bin/env python3

"""Compile and count all the instances of various kita, kicca and taddhita
suffixes in the DpdHeadword table and save to TSV."""


import pandas as pd
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths


def main_pandas():
    print("[bright_yellow]kita kicca taddhita suffix frequency")
    print("[green]processing db")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).all()

    data = []
    for i in dpd_db:
        if i.meaning_1 and i.derivative in ["kita", "kicca", "taddhita"]:
            data.append([
                i.derivative,
                i.suffix,
                i.pos,
                i.lemma_1,
                i.meaning_1,
                i.construction])

    df = pd.DataFrame(
        data, columns=[
            "derivative", "suffix", "pos", "lemma_1",
            "meaning", "construction"])

    # add counts of suffixes and pos
    df["count_suffix"] = df.groupby(
        ["derivative", "suffix"])["derivative"].transform("count")
    df["count_pos"] = df.groupby(
        ["derivative", "suffix", "pos"])["derivative"].transform("count")

    df.sort_values(
        by=[
            "count_suffix", "suffix", "derivative",
            "count_pos", "pos", "lemma_1"],
        inplace=True,
        ignore_index=True,
        ascending=[False, True, True, False, True, True],
        key=lambda x: x.map(pali_sort_key))

    df = df[[
        "count_suffix", "derivative", "suffix", "count_pos", "pos",
        "lemma_1", "meaning", "construction"]]

    df.to_csv("temp/suffixes_sorted.tsv", index=False, sep="\t")

    # csv of counts
    suffix_counts = df.value_counts(
        subset=["derivative", "suffix"],
        ascending=False).rename("count")
    suffix_counts.to_csv("temp/suffix_counts.tsv", sep="\t")

    print(df)
    print("[green]csv saved")


if __name__ == "__main__":
    main_pandas()
