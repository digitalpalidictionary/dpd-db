#!/usr/bin/env python3

"""Generates all csvs for anki from the dps-full.csv. Can enable/disable what is needed. https://sasanarakkha.github.io/study-tools/ """

import pandas as pd
import os
from dps.tools.paths_dps import DPSPaths as DPSPTH

from rich import print
from tools.tic_toc import tic, toc

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
    print("[bright_yellow]exporting csvs for anki from dps-full.csv.")

    # Read the CSV file
    df = pd.read_csv(DPSPTH.dps_full_path, sep="\t", dtype= str)
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
            function(df.copy(), *params)

    toc()


def sbs_per(df, sbs_ped_link):

    # Print starting message in green color
    print("[green]making sbs_per.csv.")

    # Create the 'Feedback' column using string formatting with the specified content
    df.reset_index(drop=True, inplace=True)

    df['feedback'] = df.apply(lambda row: (
        f"""{sbs_ped_link}={row['pali_1']}&entry.1433863141=SBS">Fix it here</a>"""
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


    # Sort the DataFrame by the 'sbs_index' column
    filtered_df['sbs_index'] = pd.to_numeric(filtered_df['sbs_index'], errors='coerce')
    filtered_df.sort_values(by='sbs_index', inplace=True)

    # Save the DataFrame into csv
    output_path = os.path.join(DPSPTH.anki_csvs_dps_dir, "anki_sbs.csv")
    filtered_df.to_csv(output_path, sep="\t", index=False, header=True)

    # Save the list of field names to a text file
    with open(f'{DPSPTH.sbs_anki_style_dir}/field-list-sbs.txt', 'w') as file:
        file.write('\n'.join(columns_to_keep))

    return None


def parittas(df, sbs_ped_link):

    # Print starting message in green color
    print("[green]making parittas.csv.")

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
        f"""{sbs_ped_link}={row['pali_1']}&entry.1433863141=Parittas">Fix it here</a>"""
    ), axis=1)

    # Select the columns to keep in the DataFrame
    columns_to_keep = ['id', 'pali_1', 'grammar', 'meaning_1', 'meaning_lit', 'root', 
        'root_group', 'root_sign', 'root_meaning', 'root_base', 'construction', 
        'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 'sbs_audio', 'test', 'feedback']

    # Keep only the specified columns in the DataFrame
    filtered_df = filtered_df[columns_to_keep]

    # Save the DataFrame into csv
    output_path = os.path.join(DPSPTH.anki_csvs_dps_dir, "anki_parittas.csv")
    filtered_df.to_csv(output_path, sep="\t", index=False, header=True)

    # Save the list of field names to a text file
    with open(f'{DPSPTH.sbs_anki_style_dir}/field-list-parittas.txt', 'w') as file:
        file.write('\n'.join(columns_to_keep))

    return None


def dps(df, dps_link):

    # Print starting message in green color
    print("[green]making dps.csv.")    

    # Create the 'Feedback' column using string formatting with the specified content
    df.reset_index(drop=True, inplace=True)

    df['feedback'] = df.apply(
        lambda row: (
            f"""{dps_link}={row['pali_1']}&entry.1433863141=Anki">Пожалуйста сообщите</a>."""
        ), 
        axis=1
    )

    # Select the columns to keep in the DataFrame
    columns_to_keep = ['id', 'pali_1', 'sbs_class_anki', 'sbs_category', 'grammar', 
        'neg', 'verb', 'trans', 'plus_case', 'meaning_1', 'meaning_lit', 'ru_meaning', 
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

    # Save the DataFrame into csv
    output_path = os.path.join(DPSPTH.anki_csvs_dps_dir, "anki_dps.csv")
    df.to_csv(output_path, sep="\t", index=False, header=True)

    # Save the list of field names to a text file
    with open(f'{DPSPTH.sbs_anki_style_dir}/field-list-dps.txt', 'w') as file:
        file.write('\n'.join(columns_to_keep))

    return None


def dhp(df, sbs_ped_link):

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
        f"""{sbs_ped_link}={row['pali_1']}&entry.1433863141=Parittas">Fix it here</a>"""
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

    # Save the DataFrame into csv
    output_path = os.path.join(DPSPTH.anki_csvs_dps_dir, "anki_dhp.csv")
    filtered_df.to_csv(output_path, sep="\t", index=False, header=True)

    # Save the list of field names to a text file
    with open(f'{DPSPTH.sbs_anki_style_dir}/field-list-dhp.txt', 'w') as file:
        file.write('\n'.join(columns_to_keep))

    return None


def classes(df, sbs_ped_link):

    # Print starting message in green color
    print("[green]making classes.csvs.")

    # Change the value of 'ru_meaning' and 'ru_meaning_lit' columns to an empty string
    df['ru_meaning'] = ""
    df['ru_meaning_lit'] = ""

    # Create the 'Feedback' column using string formatting with the specified content
    df.reset_index(drop=True, inplace=True)

    df['feedback'] = df.apply(lambda row: (
        f"""{sbs_ped_link}={row['pali_1']}&entry.1433863141=Vocab">Fix it here</a>"""
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
        full_file_path = os.path.join(DPSPTH.anki_csvs_dps_dir, 'pali_class', 'all', 
            file_name)
        filtered_df.to_csv(full_file_path, sep="\t", index=False, header=True)  

    # Select rows where 'sbs_class_anki' is not empty
    all_class_df = df[df['sbs_class_anki'] != ""]

    # Keep only the specified columns in the filtered DataFrame
    all_class_df = all_class_df[columns_to_keep]

    # Save the DataFrame into csv
    output_path = os.path.join(DPSPTH.anki_csvs_dps_dir, 'pali_class', "all_class.csv")
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
    output_path = os.path.join(DPSPTH.anki_csvs_dps_dir, 'pali_class', "class_upcoming.csv")
    concatenated_df.to_csv(output_path, sep="\t", index=False, header=True)

    # Save the list of field names to a text file
    with open(f'{DPSPTH.sbs_anki_style_dir}/field-list-vocab-class.txt', 'w') as file:
        file.write('\n'.join(columns_to_keep))

    return None


def suttas_class(df, sbs_ped_link):

    # Print starting message in green color
    print("[green]making suttas_class.csv.")

    # Create the 'Feedback' column using string formatting with the specified content
    df.reset_index(drop=True, inplace=True)

    df['feedback'] = df.apply(lambda row: (
        f"""{sbs_ped_link}={row['pali_1']}&entry.1433863141=Suttas">Fix it here</a>"""
    ), axis=1)

    # Change the value of 'ru_meaning' and 'ru_meaning_lit' columns to an empty string
    df['ru_meaning'] = ""

    # Select the rows where 'sbs_class_anki' is not empty and 'root' is not empty
    filtered_df = df[(df['sbs_category'] != "")]

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

    # Keep only the specified columns in the filtered DataFrame
    filtered_df = filtered_df[columns_to_keep]

    # Save the filtered DataFrame to a CSV file without headers
    # Set header=False to exclude column names from the CSV.
    output_path = os.path.join(DPSPTH.anki_csvs_dps_dir, 'pali_class', "suttas_class.csv")
    filtered_df.to_csv(output_path, sep="\t", index=False, header=True)

    # Save the list of field names to a text file
    with open(f'{DPSPTH.sbs_anki_style_dir}/field-list-suttas-class.txt', 'w') as file:
        file.write('\n'.join(columns_to_keep))

    return None


def root_phonetic_class(df, sbs_ped_link):

    # Print starting message in green color
    print("[green]making root and phonetic_class.csvs.")

    # Create the 'Feedback' column using string formatting with the specified content
    df.reset_index(drop=True, inplace=True)

    df['feedback'] = df.apply(lambda row: (
        f"""{sbs_ped_link}={row['pali_1']}&entry.1433863141=Roots">Fix it here</a>"""
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

    # Save the filtered DataFrame to a CSV file without headers
    # Set header=False to exclude column names from the CSV.
    output_path = os.path.join(DPSPTH.anki_csvs_dps_dir, 'pali_class', "roots_class.csv")
    root_df.to_csv(output_path, sep="\t", index=False, header=True)

    output_path = os.path.join(DPSPTH.anki_csvs_dps_dir, 'pali_class', "phonetic_class.csv")
    phonetic_df.to_csv(output_path, sep="\t", index=False, header=True)

    # Save the list of field names to a text file
    with open(f'{DPSPTH.sbs_anki_style_dir}/field-list-roots-class.txt', 'w') as file:
        file.write('\n'.join(columns_to_keep))

    return None


if __name__ == "__main__":
    main()