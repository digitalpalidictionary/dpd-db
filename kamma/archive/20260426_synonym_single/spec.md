# Spec — synonym_single

## Overview
Adapt the workflow from `db_tests/single/add_synonym_variant.py` into a new, simpler script `scripts/add/synonym_single.py` that suggests synonym matches between words that each have a **single** cleaned meaning. The TUI must be minimal so the user can review and accept suggestions quickly.

## What it should do
- Iterate over `DpdHeadword` rows.
- For each row, compute `clean_meaning(meaning_1)`.
- Treat the row as a "single-meaning word" only if the cleaned `meaning_1` contains **no `; ` separator** (i.e. exactly one meaning after cleaning).
- Group these single-meaning words by `(pos, cleaned_meaning)`. (Grouping by pos isn't an exclusion — it's a refinement so only same-pos words are proposed as synonyms of each other.)
- For each group with ≥2 distinct lemmas:
  - Skip if the `pos:meaning` key is in the exceptions JSON (`syn_var_exceptions_path`, reused from the existing script).
  - For each headword in the group, compute the candidate-synonym set = other lemmas in the group, minus any candidate already present in that headword's `synonym`, `variant`, `var_text`, or `var_phonetic` field.
  - If after filtering at least one headword would gain a real new synonym, present the group; otherwise skip silently.
- Show the user a compact view of the group and prompt **y / n / s / q**:
  - **y** → add the cross-synonyms to every headword in the group (preserving existing synonyms, deduped, sorted via `pali_list_sorter`), commit.
  - **n** → append `pos:meaning` to the exceptions JSON.
  - **s** → skip this group, do nothing.
  - **q** → quit cleanly.
- Copy a `db_search_string` of the group's lemmas to the clipboard before each prompt (matches existing UX).

## Assumptions & uncertainties
- Reuse `tools.syn_var_exceptions_path` (same JSON file as the existing script). The exception keys follow the `pos:meaning` shape used by `find_single_meanings` in the original — that file already mixes `[noun] meaning` and `pos:meaning` keys; we use `pos:meaning` for new entries to match `find_single_meanings`.
- Per the user's choice, we do **not** filter out `pron`, `sandhi`, or words with case/person grammar markers. If this produces too much noise, that filter can be added later.
- "Single meaning" is defined on the **cleaned** meaning (after `clean_meaning`), so a row whose raw `meaning_1` is `"foo; (comm) bar"` cleans to `"foo"` and counts as single-meaning.
- The variant exclusion is **per-pair**: a candidate `X` is excluded from being suggested as a synonym for headword `Y` only if `X` already appears in `Y.variant_list`, `Y.var_text`, or `Y.var_phonetic`. We do not globally remove variant words from the matching pool.
- `var_text` and `var_phonetic` are plain strings on `DpdHeadword`. We compare candidate lemmas against these via simple substring or split match — exact format unclear; will inspect a few rows during implementation and pick the simplest correct approach (likely split on `, ` like `synonym`/`variant`).
- Reuses `clean_meaning` from the existing script; we'll import it rather than duplicate.

## Constraints
- Follows project conventions: type hints (modern syntax), `Path` from `pathlib`, no `sys.path` hacks, absolute imports.
- Uses `tools.printer.printer` for output, `rich.prompt.Prompt` for input, `pyperclip` for clipboard — same stack as the original.
- Does not mutate `var_text`, `var_phonetic`, or `variant` — only writes to `synonym`.
- Single commit per accepted group (matches the original's pattern).

## How we'll know it's done
- `uv run python -m scripts.add.synonym_single` (or `python scripts/add/synonym_single.py`) launches the TUI.
- The script prints a count of single-meaning groups discovered.
- Pressing `y` on a real group writes new synonyms into the affected headwords; verifying via a SQL query shows the expected `synonym` value.
- Pressing `n` appends to the exceptions JSON; re-running skips that group.
- Pressing `q` exits cleanly with no traceback.

## What's not included
- No variant/dual-meaning logic (those stay in `add_synonym_variant.py`).
- No automatic adding of words to `variant`/`var_text`/`var_phonetic`.
- No deletion of existing synonyms.
- No GUI integration — terminal only.
