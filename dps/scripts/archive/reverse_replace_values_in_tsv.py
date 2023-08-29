import csv
from dps.tools.paths_dps import DPSPaths as DPSPTH

def reverse_replace_values_in_tsv():
    replacements = {
        'family_set': 'dps_family_set',
        'grammar': 'dps_grammar',
        'pos': 'dps_pos',
        'suffix': 'dps_suffix',
        'verb': 'dps_verb',
        'ru.ru_meaning': 'dps_ru_meaning',
        'ru.ru_meaning_lit': 'dps_ru_meaning_lit',
        'sbs.sbs_meaning': 'dps_sbs_meaning',
        'ru.ru_notes': 'dps_ru_notes',
        'sbs.sbs_example_1': 'dps_sbs_example_1',
        'sbs.sbs_example_2': 'dps_sbs_example_2',
        'sbs.sbs_example_3': 'dps_sbs_example_3',
        'sbs.sbs_example_4': 'dps_sbs_example_4',
    }

    modified_rows = []

    # Read the replaced TSV and replace values to original
    with open(DPSPTH.dps_internal_tests_replaced_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        for row in reader:
            modified_row = {}
            for key, value in row.items():
                if value in replacements:
                    modified_row[key] = replacements[value]
                else:
                    modified_row[key] = value
            modified_rows.append(modified_row)

        # Ensure fieldnames is not None before proceeding
        if reader.fieldnames is None:
            raise ValueError("Fieldnames could not be determined from the TSV.")

        # Write the original values back to the main TSV
        with open(DPSPTH.dps_internal_tests_path, 'w', newline="") as writefile:
            writer = csv.DictWriter(writefile, fieldnames=reader.fieldnames, delimiter="\t")
            writer.writeheader()
            for modified_row in modified_rows:
                writer.writerow(modified_row)

# reverse_replace_values_in_tsv()

def replace_values_in_tsv():
    replacements = {
        'dps_family_set': 'family_set',
        'dps_grammar': 'grammar',
        'dps_pos': 'pos',
        'dps_suffix': 'suffix',
        'dps_verb': 'verb',
        'dps_ru_meaning': 'ru.ru_meaning',
        'dps_ru_meaning_lit': 'ru.ru_meaning_lit',
        'dps_sbs_meaning': 'sbs.sbs_meaning',
        'dps_ru_notes': 'ru.ru_notes',
        'dps_sbs_example_1': 'sbs.sbs_example_1',
        'dps_sbs_example_2': 'sbs.sbs_example_2',
        'dps_sbs_example_3': 'sbs.sbs_example_3',
        'dps_sbs_example_4': 'sbs.sbs_example_4',
    }

    modified_rows = []

    # Read the TSV and replace values as required
    with open(DPSPTH.dps_internal_tests_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        for row in reader:
            modified_row = {}
            for key, value in row.items():
                if value in replacements:
                    modified_row[key] = replacements[value]
                else:
                    modified_row[key] = value
            modified_rows.append(modified_row)

        # Ensure fieldnames is not None before proceeding
        if reader.fieldnames is None:
            raise ValueError("Fieldnames could not be determined from the TSV.")

        # Write the modified rows to the TSV
        with open(DPSPTH.dps_internal_tests_replaced_path, 'w', newline="") as writefile:
            writer = csv.DictWriter(writefile, fieldnames=reader.fieldnames, delimiter="\t")
            writer.writeheader()
            for modified_row in modified_rows:
                writer.writerow(modified_row)


replace_values_in_tsv()