#!/usr/bin/env python3

"""A template for filtering the DPD database and exporting to .xlsx."""

import sqlite3
import pandas as pd


def connect_to_db(db_path):
    """Connect to the SQLite database."""
    conn = sqlite3.connect(db_path)
    return conn


def table_to_dataframe(conn, table_name):
    """Convert a table into a DataFrame."""
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)

    # copy meaning_2 to empty meaning_1
    df['meaning_1'] = df['meaning_1'].replace("", pd.NA)
    df["meaning_1"] = df["meaning_1"].fillna(df["meaning_2"])
    return df


def export_to_xlsx(df, file_path, columns_to_show):
    """Export the DataFrame to an .xlsx file, showing only specified columns."""
    
    # Select only the specified columns from the DataFrame
    selected_df = df[columns_to_show]
    
    # Export the selected DataFrame to an .xlsx file
    selected_df.to_excel(file_path, index=False)


def main():
    print("~"*50)

    # where is the db located on your computer?
    db_path = "dpd.db"

    # what table would you like to access?
    table_name = "dpd_headwords"

    # this connects to the db and makes a pandas dataframe - nothing to change here
    conn = connect_to_db(db_path)
    df = table_to_dataframe(conn, table_name)

    try:

        # here's some logic to filter the database, adapt this part to your needs
        # you can have as many or as few filter criteria as you want here

        filtered_df = df

        filtered_df = filtered_df[
            filtered_df["trans"] == "ditrans"]
        
        filtered_df = filtered_df[
            filtered_df["plus_case"].str.contains("\\+acc")]
        
        filtered_df = filtered_df[
            filtered_df["pos"] == "pr"]

        # which columns do you want in the excel file?
        columns_to_show = ["lemma_1", "grammar", "trans", "meaning_1", "root_key"]

        # which column do you want to sort by?
        columns_to_sort = ["root_key"]
        sorted_df = filtered_df.sort_values(by=columns_to_sort, ascending=True)

        # where would you like to save the output file?
        output_file_path = "temp/dpd_db_filter.xlsx"
        
        # export to excel file
        export_to_xlsx(sorted_df, output_file_path, columns_to_show)

        print(f"DPD data exported to {output_file_path}")
        print("~"*50)
    
    except Exception as e:
        print("there was an error exporting the file")
        print(e)
    
    conn.close()


if __name__ == "__main__":
    main()
