import pickle

from dps.tools.paths_dps import DPSPaths

dpspth = DPSPaths()

def serialize_dictionary(dict_path, output_path):
    with open(dict_path, 'r', encoding='utf-8') as f:
        custom_words = set(f.read().splitlines())
    with open(output_path, 'wb') as f:
        pickle.dump(custom_words, f)

# Run this once to serialize the dictionary
serialize_dictionary(dpspth.ru_user_dict_path, dpspth.ru_user_dict_pckl_path)

