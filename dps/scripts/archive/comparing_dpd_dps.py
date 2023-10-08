# comparing dpd and dps and moving uniaue enteries to csv

import csv
from os.path import basename

csv_file = '../spreadsheets/dps-dpd-ex.csv'

with open(csv_file) as f, \
        open('../spreadsheets/to-merge/meaning_1.csv', 'w') as meaning_1, \
        open('../spreadsheets/to-merge/meaning_lit.csv', 'w') as meaning_lit, \
        open('../spreadsheets/to-merge/root_pali.csv', 'w') as root_pali, \
        open('../spreadsheets/to-merge/root_base.csv', 'w') as root_base, \
        open('../spreadsheets/to-merge/compound_type.csv', 'w') as compound_type, \
        open('../spreadsheets/to-merge/compound_construction.csv', 'w') as compound_construction, \
        open('../spreadsheets/to-merge/sanskrit.csv', 'w') as sanskrit, \
        open('../spreadsheets/to-merge/notes.csv', 'w') as notes:
    dict_reader = csv.DictReader(f, delimiter='\t')
    out_files = [meaning_1, meaning_lit, root_pali, root_base, compound_type, compound_construction, sanskrit, notes]
    dict_writers = {}
    for file in out_files:
        name = basename(file.name)[:-4]
        if name.startswith('meaning'):
            headings = ['id', 'pali_1', 'sbs_index', 'sbs_class_anki', 'sbs_category', 'meaning_1', 'meaning_lit']
        else:
            headings = ['id', 'pali_1', 'sbs_class_anki', 'sbs_index', 'sbs_category',  name]
        dict_writers[name] = csv.DictWriter(file, headings)
        dict_writers[name].writeheader()

    for row in dict_reader:
        for name in dict_writers.keys():
            dpd_name = 'DPD_' + name
            if row[name] and not row[dpd_name]:
                if name.startswith('meaning'):
                    filtered_row = {'id': row['id'], 'pali_1': row['pali_1'],
                                    'meaning_1': row['meaning_1'], 'meaning_lit': row['meaning_lit']}
                else:
                    filtered_row = {
                        'id': row['id'], 'pali_1': row['pali_1'], name: row[name]}
                dict_writers[name].writerow(filtered_row)
