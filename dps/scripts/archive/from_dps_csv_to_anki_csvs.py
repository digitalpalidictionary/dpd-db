#!/usr/bin/env python3

"""Generates all csvs for anki from the dps-full.csv. Can enable/disable what is needed. https://sasanarakkha.github.io/study-tools/ """

import pandas as pd
import os
import datetime

from rich.console import Console

from dps.tools.paths_dps import DPSPaths
from tools.tic_toc import tic, toc

console = Console()

dpspth = DPSPaths()

current_date = datetime.date.today().strftime("%d-%m")

# Dictionary of functions and whether they are enabled
function_status = {
    "sbs_per": True,
    "parittas": True,
    "dps": True,
    "dhp": True,
    "classes": True,
    "suttas_class": True,
    "root_phonetic_class": True,
}

sbs_ped_link = 'Spot a mistake? <a class="link" href="https://docs.google.com/forms/d/e/1FAIpQLScNC5v2gQbBCM3giXfYIib9zrp-WMzwJuf_iVXEMX2re4BFFw/viewform?usp=pp_url&entry.438735500'

dps_link = 'Нашли ошибку? <a class="link" href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&entry.438735500'


def main():

    tic()

    # Print starting message in yellow color
    console.print("[bold bright_yellow]exporting csvs for anki from dps-full.csv.")

    # Read the CSV file
    df = pd.read_csv(dpspth.dps_full_path, sep="\t", dtype= str)
    df.fillna("", inplace=True)


    # Check where 'meaning_1' is empty, 'meaning_lit' is not empty, and 'meaning_2' contains " lit."
    lit_condition_mask = (
        (df['meaning_1'].str.strip() == "")
        & (df['meaning_lit'].str.strip() != "")
        & (df['meaning_2'].str.contains(" lit."))
    )

    # Use .loc to only modify rows where 'link' is not empty
    df.loc[df['link'] != '', 'link'] = '<a class="link" href="' + df['link'] + '">Wiki link</a>'


    # Remove everything after " lit." in 'meaning_2' for the rows matching the condition
    df.loc[lit_condition_mask, 'meaning_2'] = df.loc[lit_condition_mask, 'meaning_2'].apply(lambda x: x.split("; lit.")[0])

    # Now, replace 'meaning_1' with 'meaning_2' if 'meaning_1' is empty
    empty_meaning_mask = df['meaning_1'].str.strip() == ""
    df.loc[empty_meaning_mask, 'meaning_1'] = df.loc[empty_meaning_mask, 'meaning_2']


    # Dictionary of function names to function objects
    function_mapping = {
        "sbs_per": (sbs_per, [sbs_ped_link]),
        "parittas": (parittas, [sbs_ped_link]),
        "dps": (dps, [dps_link]),
        "dhp": (dhp, [sbs_ped_link]),
        "classes": (classes, [sbs_ped_link]),
        "suttas_class": (suttas_class, [sbs_ped_link]),
        "root_phonetic_class": (root_phonetic_class, [sbs_ped_link]),
    }

    # Iterate over the functions
    for function_name, (function, params) in function_mapping.items():
        if function_status.get(function_name, False):
            df_result = function(df.copy(), *params)
            if function_name == 'parittas':
                for index, row in df_result.iterrows():
                    if row['sbs_example_1'] == "":
                        console.print(f"[bold red]no example for ID: {row['id']}")
            else:
                # Check if any of the sbs_example columns are empty for each row
                for index, row in df_result.iterrows():
                    if row['sbs_example_1'] == "" and row['sbs_example_2'] == "" and row['sbs_example_3'] == "" and row['sbs_example_4'] == "":
                        console.print(f"[bold red]no example for ID: {row['id']}")


    toc()


def sbs_per(df, sbs_ped_link):

    # Print starting message in green color
    console.print("[bold green]making sbs_per.csv.")

    # Create the 'Feedback' column using string formatting with the specified content
    df.reset_index(drop=True, inplace=True)

    df['feedback'] = df.apply(lambda row: (
        f"""{sbs_ped_link}={row['pali_1']}&entry.1433863141=SBS-{current_date}">Fix it here</a>"""
    ), axis=1)

    # Change the value of 'ru_meaning' and 'ru_meaning_lit' columns to an empty string
    df['ru_meaning'] = ""

    # Select the rows where 'sbs_class_anki' is not empty and 'root' is not empty
    filtered_df = df[(df['sbs_index'] != "")]

    # Select the columns to keep in the DataFrame
    columns_to_keep = ['id', 'pali_1', 'grammar', 'neg', 'verb', 'trans', 'plus_case',
        'meaning_1', 'meaning_lit', 'ru_meaning', 'sbs_meaning', 'sanskrit', 
        'sanskrit_root', 'sanskrit_root_meaning', 'sanskrit_root_class', 'root', 
        'root_has_verb', 'root_group', 'root_sign', 'root_meaning', 'root_base', 
        'construction', 'derivative', 'suffix', 'phonetic', 'compound_type', 
        'compound_construction', 'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 
        'sbs_chant_pali_1', 'sbs_chant_eng_1', 'sbs_chapter_1', 'sbs_source_2',
        'sbs_sutta_2', 'sbs_example_2', 'sbs_chant_pali_2', 'sbs_chant_eng_2', 
        'sbs_chapter_2', 'sbs_source_3', 'sbs_sutta_3', 'sbs_example_3', 
        'sbs_chant_pali_3', 'sbs_chant_eng_3', 'sbs_chapter_3', 'sbs_source_4', 
        'sbs_sutta_4', 'sbs_example_4', 'sbs_chant_pali_4', 'sbs_chant_eng_4', 
        'sbs_chapter_4', 'antonym', 'synonym', 'variant', 'commentary', 'notes', 
        'sbs_notes', 'link', 'sbs_index', 'sbs_audio', 'test', 'feedback']

    # Keep only the specified columns in the DataFrame
    filtered_df = filtered_df[columns_to_keep]

    # Replace all spaces with underscores in the specified columns
    columns_to_replace = ['sbs_chant_pali_1', 'sbs_chant_pali_2', 'sbs_chant_pali_3', 
        'sbs_chant_pali_4']
    filtered_df[columns_to_replace] = filtered_df[columns_to_replace].replace(' ', '-', 
        regex=True)

    # Create the new column 'tags' by combining the values from the specified columns
    filtered_df['tags'] = filtered_df.apply(
        lambda row: ' '.join(
            [
                row['sbs_chant_pali_1'],
                row['sbs_chant_pali_2'],
                row['sbs_chant_pali_3'],
                row['sbs_chant_pali_4']
            ]
        ), 
        axis=1
    )

    row_count = len(filtered_df)
    console.print(f"Number of rows: [bold]{row_count}[/bold]")

    # Sort the DataFrame by the 'sbs_index' column
    filtered_df['sbs_index'] = pd.to_numeric(filtered_df['sbs_index'], errors='coerce')
    filtered_df.sort_values(by='sbs_index', inplace=True)

    # Save the DataFrame into csv
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, "anki_sbs.csv")
    filtered_df.to_csv(output_path, sep="\t", index=False, header=True)

    # Add 'marks' to the list of columns to keep
    columns_to_keep.append('marks')

    if dpspth.sbs_anki_style_dir:
        # Save the list of field names to a text file
        with open(f'{dpspth.sbs_anki_style_dir}/field-list-sbs.txt', 'w') as file:
            file.write('\n'.join(columns_to_keep))
    else:
        console.print("[bold red]no path to sbs_anki_style_dir")

    return filtered_df


def parittas(df, sbs_ped_link):

    # Print starting message in green color
    console.print("[bold green]making parittas.csv.")

    # Create a list of the values you want to filter for
    chant_names = ["Maṅgala-sutta", "Ratana-sutta", "Karaṇīya-metta-sutta"]

    # Use the 'isin()' method to filter rows based on the values in the 
    # 'sbs_chant_pali_1' or 'sbs_chant_pali_2' columns
    filtered_df = df[
        df['sbs_chant_pali_1'].isin(chant_names) |
        df['sbs_chant_pali_2'].isin(chant_names)
    ]

    # Drop duplicates to avoid having multiple occurrences of the same row in the output
    filtered_df = filtered_df.drop_duplicates()

    # Replace the columns 'sbs_source_1','sbs_sutta_1', 'sbs_example_1' with 
    # 'sbs_source_2', 'sbs_sutta_2', 'sbs_example_2' for the rows where 
    # 'sbs_chant_pali_2' matches the specified chants and 'sbs_chant_pali_1' doesn't
    replacement_mask = (filtered_df['sbs_chant_pali_2'].isin(chant_names)) & \
        (~filtered_df['sbs_chant_pali_1'].isin(chant_names))

    filtered_df.loc[replacement_mask, ['sbs_source_1', 'sbs_sutta_1', 
        'sbs_example_1']] = (
        filtered_df.loc[replacement_mask, ['sbs_source_2', 'sbs_sutta_2', 
        'sbs_example_2']].values
    )

    # Sort the DataFrame by the 'sbs_sutta_1' column
    filtered_df.sort_values(by='sbs_sutta_1', inplace=True)

    # Create the 'Feedback' column using string formatting with the specified content
    filtered_df.reset_index(drop=True, inplace=True)

    filtered_df['feedback'] = filtered_df.apply(lambda row: (
        f"""{sbs_ped_link}={row['pali_1']}&entry.1433863141=Parittas-{current_date}">Fix it here</a>"""
    ), axis=1)

    # Select the columns to keep in the DataFrame
    columns_to_keep = ['id', 'pali_1', 'grammar', 'meaning_1', 'meaning_lit', 'root', 
        'root_group', 'root_sign', 'root_meaning', 'root_base', 'construction', 
        'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 'sbs_audio', 'test', 'feedback']

    # Keep only the specified columns in the DataFrame
    filtered_df = filtered_df[columns_to_keep]

    row_count = len(filtered_df)
    console.print(f"Number of rows: [bold]{row_count}[/bold]")

    # Save the DataFrame into csv
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, "anki_parittas.csv")
    filtered_df.to_csv(output_path, sep="\t", index=False, header=True)

    # Add 'marks' to the list of columns to keep
    columns_to_keep.append('marks')

    if dpspth.sbs_anki_style_dir:
        # Save the list of field names to a text file
        with open(f'{dpspth.sbs_anki_style_dir}/field-list-parittas.txt', 'w') as file:
            file.write('\n'.join(columns_to_keep))
    else:
        console.print("[bold red]no path to sbs_anki_style_dir")

    return filtered_df


def dps(df, dps_link):

    # Print starting message in green color
    console.print("[bold green]making dps.csv.")    

    # Create the 'Feedback' column using string formatting with the specified content
    df.reset_index(drop=True, inplace=True)

    df = df[df['ru_meaning'] != ""].copy()


    # Filter rows where at least one of the sbs_example columns is not empty
    df = df[df[['sbs_example_1', 'sbs_example_2', 'sbs_example_3', 'sbs_example_4']].apply(lambda row: row.ne("").any(), axis=1)]


    df.loc[:, 'feedback'] = df.apply(lambda row: (
            f"""{dps_link}={row['pali_1']}&entry.1433863141=SBS-{current_date}">Fix it here</a>"""
        ), axis=1)

    # Select the columns to keep in the DataFrame
    columns_to_keep = ['id', 'pali_1', 'sbs_class_anki', 'sbs_category', 'sbs_class', 
    'grammar', 'neg', 'verb', 'trans', 'plus_case', 'meaning_1', 'meaning_lit', 'ru_meaning', 
    'ru_meaning_lit', 'sbs_meaning', 'sanskrit', 'sanskrit_root', 
    'sanskrit_root_meaning', 'sanskrit_root_class', 'root', 'root_has_verb', 
    'root_group', 'root_sign', 'root_meaning', 'root_base', 'construction', 
    'derivative', 'suffix', 'phonetic', 'compound_type', 'compound_construction', 
    'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 'sbs_chant_pali_1', 
    'sbs_chant_eng_1', 'sbs_chapter_1', 'sbs_source_2', 'sbs_sutta_2', 
    'sbs_example_2', 'sbs_chant_pali_2', 'sbs_chant_eng_2', 'sbs_chapter_2', 
    'sbs_source_3', 'sbs_sutta_3', 'sbs_example_3', 'sbs_chant_pali_3', 
    'sbs_chant_eng_3', 'sbs_chapter_3', 'sbs_source_4', 'sbs_sutta_4', 
    'sbs_example_4', 'sbs_chant_pali_4', 'sbs_chant_eng_4', 'sbs_chapter_4', 
    'antonym', 'synonym', 'variant', 'commentary', 'notes', 'sbs_notes', 
    'ru_notes', 'link', 'sbs_index', 'sbs_audio', 'test', 'feedback']

    # Keep only the specified columns in the DataFrame
    df = df[columns_to_keep]

    row_count = len(df)
    console.print(f"Number of rows: [bold]{row_count}[/bold]")

    # Save the DataFrame into csv
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, "anki_dps.csv")
    df.to_csv(output_path, sep="\t", index=False, header=True)

    # Add 'marks' to the list of columns to keep
    columns_to_keep.append('marks')

    if dpspth.sbs_anki_style_dir:
        # Save the list of field names to a text file
        with open(f'{dpspth.sbs_anki_style_dir}/field-list-dps.txt', 'w') as file:
            file.write('\n'.join(columns_to_keep))

    else:
        console.print("[bold red]no path to sbs_anki_style_dir")

    return df


def dhp(df, sbs_ped_link):

    # Print starting message in green color
    console.print("[bold green]making dhp.csv.")

    # Change the value of 'ru_meaning' and 'ru_meaning_lit' columns to an empty string
    df['ru_meaning'] = ""   

    # Define the conditions for filtering
    conditions = [
        (df[f'sbs_source_{i}'].str.contains('DHP', case=False)) & 
        (df[f'sbs_sutta_{i}'].str.contains('vaggo', case=False))
        for i in range(1, 5)
    ]

    # Combine the conditions with 'OR' (|) to get the final filtering condition
    final_condition = conditions[0]
    for condition in conditions[1:]:
        final_condition |= condition

    # Apply the filtering condition to get the filtered DataFrame
    filtered_df = df[final_condition]

    # Replace values in sbs_source_i, sbs_sutta_i, and sbs_example_i columns
    for i in range(2, 5):
        condition = (df[f'sbs_source_{i}'].str.contains('DHP', 
        case=False)) & (df[f'sbs_sutta_{i}'].str.contains('vaggo', case=False))
        df.loc[condition, 'sbs_source_1'] = df.loc[condition, f'sbs_source_{i}']
        df.loc[condition, 'sbs_sutta_1'] = df.loc[condition, f'sbs_sutta_{i}']
        df.loc[condition, 'sbs_example_1'] = df.loc[condition, f'sbs_example_{i}']

    # Drop duplicates from the filtered DataFrame
    filtered_df = filtered_df.drop_duplicates()

    # Apply the first condition and replace values in sbs_source_i, sbs_sutta_i, 
    # and sbs_example_i columns
    condition1 = conditions[0]
    df.loc[condition1, 'sbs_source_2'] = df.loc[condition1, 'sbs_source_1']
    df.loc[condition1, 'sbs_sutta_2'] = df.loc[condition1, 'sbs_sutta_1']
    df.loc[condition1, 'sbs_example_2'] = df.loc[condition1, 'sbs_example_1']

    # Apply the second condition and replace values in sbs_source_i, sbs_sutta_i, 
    # and sbs_example_i columns
    condition2 = conditions[1]
    df.loc[condition2, 'sbs_source_3'] = df.loc[condition2, 'sbs_source_1']
    df.loc[condition2, 'sbs_sutta_3'] = df.loc[condition2, 'sbs_sutta_1']
    df.loc[condition2, 'sbs_example_3'] = df.loc[condition2, 'sbs_example_1']

    # Apply the third condition and replace values in sbs_source_i, sbs_sutta_i, 
    # and sbs_example_i columns
    condition3 = conditions[2]
    df.loc[condition3, 'sbs_source_4'] = df.loc[condition3, 'sbs_source_1']
    df.loc[condition3, 'sbs_sutta_4'] = df.loc[condition3, 'sbs_sutta_1']
    df.loc[condition3, 'sbs_example_4'] = df.loc[condition3, 'sbs_example_1']

    # Combine the conditions with 'OR' (|) to get the final filtering condition
    final_condition = condition1 | condition2 | condition3

    # Apply the final filtering condition to get the filtered DataFrame
    filtered_df = df[final_condition].copy()

    # Create the 'Feedback' column using string formatting with the specified content
    filtered_df.reset_index(drop=True, inplace=True)

    filtered_df.loc[:, 'feedback'] = filtered_df.apply(lambda row: (
        f"""{sbs_ped_link}={row['pali_1']}&entry.1433863141=Parittas-{current_date}">Fix it here</a>"""
    ), axis=1)

    # Select the columns to keep in the filtered DataFrame
    columns_to_keep = ['id', 'pali_1', 'grammar', 'neg', 'verb', 'trans', 
        'plus_case', 'meaning_1', 'meaning_lit', 'ru_meaning', 'sanskrit', 
        'sanskrit_root', 'sanskrit_root_meaning', 'sanskrit_root_class', 'root', 
        'root_has_verb', 'root_group', 'root_sign', 'root_meaning', 'root_base', 
        'construction', 'derivative', 'suffix', 'phonetic', 'compound_type', 
        'compound_construction', 'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 
        'link', 'sbs_audio', 'test', 'feedback']

    # Keep only the specified columns in the filtered DataFrame
    filtered_df = filtered_df[columns_to_keep]

    # Sort the DataFrame by the 'sbs_sutta_1' column
    filtered_df.sort_values(by='sbs_source_1', inplace=True)

    row_count = len(filtered_df)
    console.print(f"Number of rows: [bold]{row_count}[/bold]")

    # Save the DataFrame into csv
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, "anki_dhp.csv")
    filtered_df.to_csv(output_path, sep="\t", index=False, header=True)

    # Add 'marks' to the list of columns to keep
    columns_to_keep.append('marks')

    if dpspth.sbs_anki_style_dir:
        # Save the list of field names to a text file
        with open(f'{dpspth.sbs_anki_style_dir}/field-list-dhp.txt', 'w') as file:
            file.write('\n'.join(columns_to_keep))

    else:
        console.print("[bold red]no path to sbs_anki_style_dir")

    return filtered_df


def classes(df, sbs_ped_link):

    # Print starting message in green color
    console.print("[bold green]making classes.csvs.")

    # Filter DataFrame with 'sbs_class_anki' not empty
    # df = df[df['sbs_class_anki'] != ""]

    # Create a mask for rows where 'ru_meaning_lit' is not an empty string
    mask = df['ru_meaning_lit'].apply(lambda x: x != "")

    # Concatenate 'ru_meaning' and 'ru_meaning_lit' with '; досл. ' for rows where 'ru_meaning_lit' is not an empty string
    df.loc[mask, 'ru_meaning'] = df.loc[mask, ['ru_meaning', 'ru_meaning_lit']].apply(lambda row: '; досл. '.join(filter(None, row)), axis=1)

    # Create a copy of the DataFrame with the original 'ru_meaning' values
    df_original = df.copy()

    # Change the value of 'ru_meaning' and 'ru_meaning_lit' columns to an empty string
    df['ru_meaning'] = ""
    df['ru_meaning_lit'] = ""

    # Create the 'Feedback' column using string formatting with the specified content
    df.reset_index(drop=True, inplace=True)

    df['feedback'] = df.apply(lambda row: (
        f"""{sbs_ped_link}={row['pali_1']}&entry.1433863141=Vocab-{current_date}">Fix it here</a>"""
    ), axis=1)

    # Get unique values in 'sbs_class_anki' column
    unique_sbs_class_values = df[df['sbs_class_anki'] != ""]["sbs_class_anki"].unique()

    # Select the columns to keep in the DataFrame
    columns_to_keep = ['id', 'pali_1', 'sbs_class_anki', 
        'grammar', 'neg', 'verb', 'trans', 'plus_case', 'meaning_1', 'meaning_lit', 
        'ru_meaning', 'sanskrit', 'sanskrit_root', 
        'sanskrit_root_meaning', 'sanskrit_root_class', 'root', 'root_has_verb', 
        'root_group', 'root_sign', 'root_meaning', 'root_base', 'construction', 
        'derivative', 'suffix', 'phonetic', 'compound_type', 'compound_construction', 
        'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 'sbs_chant_pali_1', 
        'sbs_chant_eng_1', 'sbs_chapter_1', 'sbs_source_2', 'sbs_sutta_2', 
        'sbs_example_2', 'sbs_chant_pali_2', 'sbs_chant_eng_2', 'sbs_chapter_2', 
        'sbs_source_3', 'sbs_sutta_3', 'sbs_example_3', 'sbs_chant_pali_3', 
        'sbs_chant_eng_3', 'sbs_chapter_3', 'sbs_source_4', 'sbs_sutta_4', 
        'sbs_example_4', 'sbs_chant_pali_4', 'sbs_chant_eng_4', 'sbs_chapter_4', 
        'antonym', 'synonym', 'variant', 'commentary', 'notes', 'sbs_notes', 'link', 
        'sbs_audio', 'test', 'feedback']

    # Loop through each unique value in 'sbs_class_anki' column
    for sbs_class_value in unique_sbs_class_values:
        # Filter the DataFrame for the current 'sbs_class_anki' value
        filtered_df = df[df['sbs_class_anki'] == sbs_class_value]
        
        # Keep only the specified columns in the filtered DataFrame
        filtered_df = filtered_df[columns_to_keep]
        
        # Save the filtered DataFrame to a CSV file with the corresponding class
        # value in the filename; Set header=False to remove column names in the CSV.
        file_name = f'class_{sbs_class_value}.csv'
        full_file_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', 'classes', 
            file_name)
        filtered_df.to_csv(full_file_path, sep="\t", index=False, header=True)  

    # Select rows where 'sbs_class_anki' is not empty
    all_class_df = df[df['sbs_class_anki'] != ""]

    # Keep only the specified columns in the filtered DataFrame
    all_class_df = all_class_df[columns_to_keep]

    # Save the DataFrame into csv
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', 'classes', "class_total.csv")
    all_class_df.to_csv(output_path, sep="\t", index=False, header=True)

    # Define the range of values you want to include in the 'class_upcoming.csv'
    start_value = 30
    end_value = 54

    # Initialize an empty DataFrame to concatenate filtered DataFrames
    concatenated_df = pd.DataFrame()

    # Loop through each unique value in 'sbs_class_anki' column
    for sbs_class_value in unique_sbs_class_values:
        # Convert the 'sbs_class_value' to an integer
        sbs_class_value_int = int(sbs_class_value)

        # Check if the 'sbs_class_value' as an integer falls within the desired range
        if start_value <= sbs_class_value_int <= end_value:
            # Filter the DataFrame for the current 'sbs_class_anki' value
            filtered_df = df[df['sbs_class_anki'] == sbs_class_value]

            # Keep only the specified columns in the filtered DataFrame
            filtered_df = filtered_df[columns_to_keep]

            # Append the filtered DataFrame to the concatenated DataFrame
            concatenated_df = pd.concat([concatenated_df, filtered_df])

    # Save the concatenated DataFrame to the 'class_upcoming.csv' file
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', 'classes', "class_upcoming.csv")
    concatenated_df.to_csv(output_path, sep="\t", index=False, header=True)

    # Define the range of values you want to include in the 'class_basic.csv'
    start_value = 1
    end_value = 29

    # Initialize an empty DataFrame to concatenate filtered DataFrames
    concatenated_df = pd.DataFrame()
    concatenated_ru_df = pd.DataFrame()

    # Loop through each unique value in 'sbs_class_anki' column
    for sbs_class_value in unique_sbs_class_values:
        # Convert the 'sbs_class_value' to an integer
        sbs_class_value_int = int(sbs_class_value)

        # Check if the 'sbs_class_value' as an integer falls within the desired range
        if start_value <= sbs_class_value_int <= end_value:
            # Filter the DataFrame for the current 'sbs_class_anki' value
            filtered_df = df[df['sbs_class_anki'] == sbs_class_value]

            # Filter the same for ru_meaning
            filtered_ru_df = df_original[df_original['sbs_class_anki'] == sbs_class_value]

            # Keep only the specified columns in the filtered DataFrame
            filtered_ru_df = filtered_ru_df[['id', 'ru_meaning']]

            filtered_df = filtered_df[columns_to_keep]

            # Append the filtered DataFrame to the concatenated DataFrame
            concatenated_df = pd.concat([concatenated_df, filtered_df])
            concatenated_ru_df = pd.concat([concatenated_ru_df, filtered_ru_df])

    row_count = len(concatenated_df)
    console.print(f"Number of rows (class_basic): [bold]{row_count}[/bold]")

    # Save the concatenated DataFrame to the 'class_basic.csv' file
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', "class_all.csv")
    concatenated_df.to_csv(output_path, sep="\t", index=False, header=True)

    # Save the concatenated DataFrame to the 'class_ru.csv' file
    output_path_ru = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', "class_ru.csv")
    concatenated_ru_df.to_csv(output_path_ru, sep="\t", index=False, header=True)

    # Add 'marks' to the list of columns to keep
    columns_to_keep.append('marks')

    if dpspth.sbs_anki_style_dir:
        # Save the list of field names to a text file
        with open(f'{dpspth.sbs_anki_style_dir}/field-list-vocab-class.txt', 'w') as file:
            file.write('\n'.join(columns_to_keep))

    else:
        console.print("[bold red]no path to sbs_anki_style_dir")

    return all_class_df


def suttas_class(df, sbs_ped_link):

    # Print starting message in green color
    console.print("[bold green]making suttas_class.csv.")

    # Create the 'Feedback' column using string formatting with the specified content
    df.reset_index(drop=True, inplace=True)

    df['feedback'] = df.apply(lambda row: (
        f"""{sbs_ped_link}={row['pali_1']}&entry.1433863141=Suttas-{current_date}">Fix it here</a>"""
    ), axis=1)

    # Change the value of 'ru_meaning' column to an empty string
    df['ru_meaning'] = ""

    # Select the columns to keep in the filtered DataFrame
    columns_to_keep = ['id', 'pali_1', 'sbs_category', 
        'grammar', 'neg', 'verb', 'trans', 'plus_case', 'meaning_1', 'meaning_lit', 
        'ru_meaning', 'sanskrit', 'sanskrit_root', 
        'sanskrit_root_meaning', 'sanskrit_root_class', 'root', 'root_has_verb', 
        'root_group', 'root_sign', 'root_meaning', 'root_base', 'construction', 
        'derivative', 'suffix', 'phonetic', 'compound_type', 'compound_construction', 
        'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 'sbs_source_2', 'sbs_sutta_2', 
        'sbs_example_2', 'sbs_source_3', 'sbs_sutta_3', 'sbs_example_3', 'sbs_source_4',
        'sbs_sutta_4', 'sbs_example_4', 'antonym', 'synonym', 'variant', 'commentary', 
        'notes', 'sbs_notes', 'link', 'sbs_audio', 'test', 'feedback']

    # Create a separate DataFrame with 'sbs_category' not empty

    df_with_category = df[df['sbs_category'] != ""].copy()

    # Filter those without examples
    df_with_category = df_with_category[df_with_category['sbs_category'].str.contains('_') == False]

    df_with_category = df_with_category[columns_to_keep]

    row_count = len(df_with_category)
    console.print(f"Number of rows: [bold]{row_count}[/bold]")

    # Save the whole DataFrame with 'sbs_category' not empty to a CSV file
    output_path_full = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', "suttas_class.csv")
    df_with_category.to_csv(output_path_full, sep="\t", index=False, header=True)

    # Iterate through unique values in the 'sbs_category' column
    unique_categories = df['sbs_category'].unique()
    for category in unique_categories:
        if not pd.isnull(category) and category != "":
            # Select the rows where 'sbs_category' matches the current category 
            filtered_df = df[df['sbs_category'] == category]

            # Keep only the specified columns in the filtered DataFrame
            filtered_df = filtered_df[columns_to_keep]

            # Save the filtered DataFrame to a CSV file with the name based on the category
            output_filename = f"{category}.csv"
            output_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', 'suttas', output_filename)
            filtered_df.to_csv(output_path, sep="\t", index=False, header=True)

    # Add 'marks' to the list of columns to keep
    columns_to_keep.append('marks')

    if dpspth.sbs_anki_style_dir:
        # Save the list of field names to a text file
        with open(f'{dpspth.sbs_anki_style_dir}/field-list-suttas-class.txt', 'w') as file:
            file.write('\n'.join(columns_to_keep))

    else:
        console.print("[bold red]no path to sbs_anki_style_dir")

    return df_with_category


def root_phonetic_class(df, sbs_ped_link):

    # Print starting message in green color
    console.print("[bold green]making root and phonetic_class.csvs.")

    # Create the 'Feedback' column using string formatting with the specified content
    df.reset_index(drop=True, inplace=True)

    df['feedback'] = df.apply(lambda row: (
        f"""{sbs_ped_link}={row['pali_1']}&entry.1433863141=Roots-{current_date}">Fix it here</a>"""
    ), axis=1)

    # Change the value of 'ru_meaning' and 'ru_meaning_lit' columns to an empty string
    df['ru_meaning'] = ""
    df['ru_meaning_lit'] = ""

    # Select the rows where 'sbs_class_anki' is not empty and 'root' is not empty
    root_df = df[(df['sbs_class_anki'] != "") & (df['root'] != "")]

    # Select the rows where 'sbs_class_anki' is not empty and 'phonetic' is not empty
    phonetic_df = df[(df['sbs_class_anki'] != "") & (df['phonetic'] != "")]

    # Select the columns to keep in the filtered DataFrame
    columns_to_keep = ['id', 'pali_1', 'sbs_class_anki',
        'grammar', 'neg', 'verb', 'trans', 'plus_case', 'meaning_1', 'meaning_lit', 
        'ru_meaning', 'sanskrit', 'sanskrit_root', 
        'sanskrit_root_meaning', 'sanskrit_root_class', 'root', 'root_has_verb', 
        'root_group', 'root_sign', 'root_meaning', 'root_base', 'construction', 
        'derivative', 'suffix', 'phonetic', 'compound_type', 'compound_construction', 
        'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 'sbs_source_2', 'sbs_sutta_2', 
        'sbs_example_2', 'sbs_source_3', 'sbs_sutta_3', 'sbs_example_3', 'sbs_source_4',
        'sbs_sutta_4', 'sbs_example_4', 'antonym', 'synonym', 'variant', 'commentary', 
        'notes', 'sbs_notes', 'link', 'sbs_audio', 'test', 'feedback']

    # Keep only the specified columns in the filtered DataFrame
    root_df = root_df[columns_to_keep]
    phonetic_df = phonetic_df[columns_to_keep]

    row_count = len(root_df)
    console.print(f"Number of rows (root_df): [bold]{row_count}[/bold]")

    row_count = len(phonetic_df)
    console.print(f"Number of rows (phonetic_df): [bold]{row_count}[/bold]")

    # Save the filtered DataFrame to a CSV file without headers
    # Set header=False to exclude column names from the CSV.
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', "roots_class.csv")
    root_df.to_csv(output_path, sep="\t", index=False, header=True)

    output_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', "phonetic_class.csv")
    phonetic_df.to_csv(output_path, sep="\t", index=False, header=True)

    # Add 'marks' to the list of columns to keep
    columns_to_keep.append('marks')

    if dpspth.sbs_anki_style_dir:
        # Save the list of field names to a text file
        with open(f'{dpspth.sbs_anki_style_dir}/field-list-roots-class.txt', 'w') as file:
            file.write('\n'.join(columns_to_keep))

    else:
        console.print("[bold red]no path to sbs_anki_style_dir")
        
    return root_df


if __name__ == "__main__":
    main()