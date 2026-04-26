# Plan — synonym_single

## Architecture Decisions
- **Location:** `scripts/add/synonym_single.py` — matches the user's request and the existing `scripts/add/` convention.
- **Reuse, don't duplicate:** import `clean_meaning` from `db_tests.single.add_synonym_variant` rather than copying. If that import path is brittle (script-style file), inline a small copy with a comment pointing at the source.
- **Exceptions key shape:** `f"{pos}:{cleaned_meaning}"` — same shape `find_single_meanings` uses. Shared JSON file with the existing script (`syn_var_exceptions_path`).
- **Grouping key:** `(pos, cleaned_meaning)`. Grouping by pos is a match-quality refinement, not an exclusion of any headwords.
- **Variant-field check helper:** one helper that returns the set of "already-related" tokens for a headword: `synonym_list ∪ variant_list ∪ split(var_text) ∪ split(var_phonetic)`. Used to filter candidates per pair.
- **No partial commits inside a group:** if user says `y`, all headwords in the group get updated and a single `commit()` is issued.
- **Single-file script, no helpers package:** mirrors `add_synonym_variant.py` style.

## Phase 1 — Discovery and skeleton

- [ ] Inspect `var_text` and `var_phonetic` on a handful of headwords with non-empty values to confirm format (likely comma-separated like `variant`).
  → verify: run a one-shot query in a Python REPL or scratch script printing 5 non-empty rows of each; record the format in a comment in `synonym_single.py`.
- [ ] Create `scripts/add/synonym_single.py` skeleton: imports, `GlobalVars` class (db session, exceptions load/save), `main()` calling `find_single_meaning_groups()` and `prompt_groups()`, `if __name__ == "__main__": main()`.
  → verify: `uv run python scripts/add/synonym_single.py` runs without error and prints a startup banner via `pr`.

## Phase 2 — Build the single-meaning dict

- [ ] Implement `find_single_meaning_groups(g)`: iterate `g.dpd_db`, compute `cleaned = clean_meaning(row.meaning_1)`, skip if empty or contains `"; "`, key = `f"{row.pos}:{cleaned}"`, value = list of `DpdHeadword`. Skip keys present in `g.exceptions`.
  → verify: print the count of groups with ≥2 entries; spot-check 3 groups by printing their lemmas and pos to confirm they make sense.
- [ ] Drop groups with fewer than 2 distinct lemmas.
  → verify: assert no group in the resulting dict has `len < 2`.

## Phase 3 — Per-pair candidate filtering and TUI

- [ ] Add helper `related_tokens(hw) -> set[str]` returning union of `synonym_list`, `variant_list`, tokens from `var_text`, tokens from `var_phonetic`.
  → verify: call on a few sample headwords with known data, print the resulting sets, confirm they include all expected tokens.
- [ ] Implement `prompt_groups(g)`:
  - For each `(key, headwords)` group: compute `lemma_clean` of each, build per-headword candidate set = `{other lemma_cleans} - related_tokens(headword) - {self.lemma_clean}`. If every headword's candidate set is empty, skip the group silently.
  - Otherwise print: group counter `i / total`, the cleaned meaning, and one line per headword showing `lemma_1`, `pos`, `meaning_1`, current `synonym`, current `variant`.
  - Copy `db_search_string([h.lemma_1 for h in group])` to clipboard.
  - Prompt `Prompt.ask("(y)es add, (n)o exception, (s)kip, (q)uit")`.
  → verify: dry-run the script on the live db; confirm groups display correctly and prompts respond to each key without crashing (test `s` and `q` first; do not press `y` or `n` yet).

## Phase 4 — Apply actions

- [ ] On `y`: for each headword in the group, new_synonyms = `pali_list_sorter((existing_synonym_list ∪ candidate_set) - related-other-fields)`; assign `headword.synonym = ", ".join(new_synonyms)` only if it differs from current. `g.db_session.commit()` once per accepted group. Print a small confirmation showing each updated headword's new synonym list.
  → verify: pick a known group manually before running, accept with `y`, then query the db (`sqlite3 dpd.db "select lemma_1, synonym from dpd_headwords where lemma_1 in (...)"`) and confirm the synonyms were written and sorted.
- [ ] On `n`: call `g.update_exceptions(key)`; print confirmation. Re-run the script; verify the group does not appear again.
  → verify: after pressing `n` for one group, re-run script and grep the printed groups for that meaning — it should be absent.
- [ ] On `s`: continue to next group (no db or exceptions change).
  → verify: counter advances; nothing in the db or exceptions JSON changes (check file mtime).
- [ ] On `q`: break out of the loop and run `pr.toc()` then return.
  → verify: pressing `q` exits within a second and prints the toc summary.

## Phase 5 — Polish and final verification

- [ ] Apply project-wide checks: type hints (modern), no unnecessary comments, no `sys.path` hacks, `Path` not `os.path`. Run `uv run ruff check scripts/add/synonym_single.py` and `uv run ruff format scripts/add/synonym_single.py`.
  → verify: ruff reports clean.
- [ ] Ask the user to do an end-to-end test pass on a handful of real groups (this is STOP 2, handled by the kamma flow — not a script step).
  → verify: user confirmation.
