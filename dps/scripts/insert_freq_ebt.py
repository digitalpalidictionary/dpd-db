#!/usr/bin/env python3

"""insert column of frequency count of EBTs into dpd_dps_full and add in into freq.db"""

from dps.tools.paths_dps import DPSPaths

from rich.console import Console

from tools.tic_toc import tic, toc

import pandas as pd
import sqlite3

console = Console()


def read_dataframes(dps_full_path, freq_ebt_path):
    full_df = pd.read_csv(dps_full_path, sep="\t", dtype=str)
    freq_df = pd.read_csv(freq_ebt_path, sep="\t", dtype=str)
    return full_df, freq_df


def process_dataframes(full_df, freq_df):
    full_df['pali_1_no_num'] = full_df['pali_1'].apply(lambda x: x.split()[0])
    merged_df = pd.merge(full_df, freq_df, left_on=['pali_1_no_num', 'pos'], right_on=['pali', 'pos'], how='left')
    merged_df.drop(['pali_1_no_num', 'pali'], axis=1, inplace=True)
    
    merged_df['count'] = pd.to_numeric(merged_df['count'], errors='coerce', downcast='integer')
    merged_df = merged_df.sort_values(by='count', ascending=False, na_position='last')
    
    cols = ['count', 'sbs_index'] + [col for col in merged_df.columns if col not in ['count', 'sbs_index']]
    merged_df = merged_df[cols]
    
    merged_df['id'] = merged_df['id'].astype(int)
    merged_df['count'].fillna(0, inplace=True)
    merged_df['count'] = merged_df['count'].astype(int)
    
    merged_df.fillna("", inplace=True)
    
    return merged_df


def save_to_sqlite(merged_df, db_path):
    conn = sqlite3.connect(db_path)
    merged_df.to_sql('_full_frequency', conn, if_exists='replace', index=False, dtype={'count': 'INTEGER', 'id': 'INTEGER', 'sbs_class_anki': 'INTEGER'})
    conn.close()


def main():
    tic()
    console.print("[bold bright_yellow]adding frequency count into dpd_dps_full freq.db")

    dpspth = DPSPaths()

    dps_full_path = dpspth.dpd_dps_full_path
    freq_ebt_path = dpspth.freq_ebt_path
    db_path = dpspth.freq_db_path

    full_df, freq_df = read_dataframes(dps_full_path, freq_ebt_path)
    merged_df = process_dataframes(full_df, freq_df)

    console.print("[bold green]saving into freq.db")

    save_to_sqlite(merged_df, db_path)

    toc()

if __name__ == "__main__":
    main()