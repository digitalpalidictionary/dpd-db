# Columns the contributor corpus consumers read

Database: `dpd_copy.db`. Sample: 2589 headwords (fixed seed 0: 2000 random, plus up to 200 each with empty `meaning_1`, a multi-meaning `meaning_1`, and empty `freq_data`).
Rounds: 2. Final run: 0 raises.
`has_textual_occurrence` took the frequency path 190 times (empty `meaning_1`) in the final run.

## Final set S (18 columns with `id`)

| Column | Started in S | First needed by |
|---|---|---|
| construction | yes | start list |
| family_root | yes | start list |
| family_word | no | find_phonetic_variants |
| freq_data | yes | start list |
| grammar | yes | start list |
| inflections | yes | start list |
| inflections_api_ca_eva_iti | yes | start list |
| lemma_1 | yes | start list |
| meaning_1 | yes | start list |
| pos | yes | start list |
| root_base | yes | start list |
| root_key | yes | start list |
| root_sign | yes | start list |
| synonym | yes | start list |
| var_phonetic | yes | start list |
| var_text | yes | start list |
| variant | yes | start list |
| id | primary key | always loaded |

## Notes
- `raiseload` only adds columns that raise. A column in the start list that no consumer reads would not raise, so S may be larger than the minimum. Removing each column in turn would find the minimum; the gain is small next to dropping the other 41 columns, so it is not done unless the gate asks for it.
- `freq_data` is read: the frequency path ran 190 times in the sample (`tools/synonym_variant.py:351-358`). Dropping it would change detector results for rows with an empty `meaning_1`. The variant `corpus_slim_nofreq` is a memory ceiling only.
- The sample and the fixed seed are in `find_columns.py`. Re-run: `PYTHONPATH=. uv run kamma/threads/20261102_contrib_mem_savings/artifacts/find_columns.py --db <copy> --out <md>`.
