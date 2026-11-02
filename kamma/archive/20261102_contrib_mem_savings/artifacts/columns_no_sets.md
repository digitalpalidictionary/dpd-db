# Columns the contributor corpus consumers read

Database: `dpd_copy.db`. Sample: 2589 headwords (fixed seed 0: 2000 random, plus up to 200 each with empty `meaning_1`, a multi-meaning `meaning_1`, and empty `freq_data`).
Rounds: 2. Final run: 0 raises. Inflection-set consumer: off (--no-sets).
`has_textual_occurrence` took the frequency path 190 times (empty `meaning_1`) in the final run.

## Final set S (16 columns with `id`)

| Column | Started in S | First needed by |
|---|---|---|
| construction | yes | start list |
| family_root | yes | start list |
| family_word | no | find_phonetic_variants |
| freq_data | yes | start list |
| grammar | yes | start list |
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
