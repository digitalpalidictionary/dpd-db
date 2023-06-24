import pandas as pd
import numpy as np
from pandas_ods_reader import read_ods 
import re
from natsort import index_natsorted

df_dpd = pd.read_csv("../csvs/dpd-full.csv", sep="\t", dtype= str)
df_dpd.fillna("")


df_dpd["id"] = df_dpd["ID"]

df_dpd["DPD_source_1"] = df_dpd["Source1"]
df_dpd["DPD_sutta_1"] = df_dpd["Sutta1"]
df_dpd["DPD_example_1"] = df_dpd["Example1"]
df_dpd["DPD_source_2"] = df_dpd["Source 2"]
df_dpd["DPD_sutta_2"] = df_dpd["Sutta2"]
df_dpd["DPD_example_2"] = df_dpd["Example 2"]

df_dpd["DPD_pos"] = df_dpd['POS']
df_dpd["DPD_grammar"] = df_dpd['Grammar']
# df_dpd["DPD_derived_from"] = df_dpd['derived_from']
# df_dpd["DPD_neg"] = df_dpd['neg']
# df_dpd["DPD_verb"] = df_dpd['verb']
# df_dpd["DPD_trans"] = df_dpd['trans']
df_dpd["DPD_plus_case"] = df_dpd['Case']
df_dpd["DPD_meaning_1"] = df_dpd["Meaning IN CONTEXT"]
df_dpd["DPD_meaning_lit"] = df_dpd["Literal Meaning"]
df_dpd["DPD_root_pali"] = df_dpd["Pāli Root"]
df_dpd["DPD_root_base"] = df_dpd["Base"]
df_dpd["DPD_construction"] = df_dpd["Construction"]
df_dpd["DPD_sanskrit"] = df_dpd["Sanskrit"]
df_dpd["DPD_derivative"] = df_dpd["Derivative"]
df_dpd["DPD_phonetic"] = df_dpd["Phonetic Changes"]
df_dpd["DPD_suffix"] = df_dpd["Suffix"]
df_dpd["DPD_compound_type"] = df_dpd["Compound"]
df_dpd["DPD_compound_construction"] = df_dpd["Compound Construction"]
df_dpd["DPD_variant"] = df_dpd["Variant – same constr or diff reading"]
df_dpd["DPD_commentary"] = df_dpd["Commentary"]
df_dpd["DPD_notes"] = df_dpd["Notes"]
df_dpd["DPD_stem"] = df_dpd["Stem"]
df_dpd["DPD_pattern"] = df_dpd["Pattern"]

df_dpd = df_dpd[['id', 'DPD_pos', 'DPD_grammar', 'DPD_plus_case', 'DPD_meaning_1', 'DPD_meaning_lit', 'DPD_root_pali', 'DPD_root_base', 'DPD_construction', 'DPD_derivative', 'DPD_suffix', 'DPD_phonetic', 'DPD_compound_type', 'DPD_compound_construction', 'DPD_sanskrit', 'DPD_variant', 'DPD_commentary', 'DPD_notes', 'DPD_source_1', 'DPD_sutta_1', 'DPD_example_1', 'DPD_source_2', 'DPD_sutta_2', 'DPD_example_2', 'DPD_stem', 'DPD_pattern']]

df_dps = pd.read_csv("dps.csv", sep="\t", dtype= str)
df_dps.fillna("")

# df_dps = df_dps.drop(['DPD'], axis = 1)

df_dps_merged = pd.merge(df_dps, df_dpd)

df_dps_merged.to_csv("dps-dpd-ex.csv", sep="\t", index=None)
