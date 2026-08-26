# Plan: missing present-tense verbs

## Architecture Decisions
- **One script per phase, shared helpers in the first.** `scripts/find/missing_pr_verbs.py`
  owns the wanted-verb collection, corpus loading and field derivation. Phase 2 extends it
  with a `--paradigm` flag rather than a second script — same inputs, same outputs, one
  extra search pass. Phase 3 gets its own script; its inputs are entirely different.
- **Reuse `verb_finder`'s parser.** `parse_grammar`, `lemma_clean` and `DERIVED_POS` already
  handle the grammar conventions and are proven against the live db. Import, don't re-derive.
- **Reuse `inflection_templates`.** Phase 2 reads the real stem/ending grid for the four
  present patterns instead of hand-rolling endings.
- **TSV via `verb_finder.write_tsv`.** Same helper, same list-of-dicts shape.
- **X JSON written to the gui2 path only on an explicit flag.** That file is the editor's
  live queue; overwriting it unasked would discard a batch in progress.

## Phase 1 — the 664, exact form

- [x] Create `scripts/find/missing_pr_verbs.py`: imports, `OUTPUT_DIR = pth.temp_dir /
      "missing_pr_verbs"`, `main()` with `pr.tic()`/`pr.toc()`.
      → verify: `uv run ruff check` and `uv run pyright` both clean.

- [x] `collect_wanted_verbs(db)` → `dict[str, list[dict]]` mapping each referenced-but-
      missing verb to the derived-form entries that name it (lemma, pos, family_root,
      root_key). Skips root references, multi-word targets, and bare `na`/`no`.
      → verify: 664 verbs, 862 dependent entries — matches the spec's established facts.

- [x] `load_corpus_freq(pth)` → `dict[str, Counter[str]]` for cst, sc, bjt from the
      `*_freq.json` files.
      → verify: 975613 / 169419 / 500251 distinct forms respectively.

- [x] `derive_fields(verb, referring_entries)` → `dict[str, str]` filling lemma_1, lemma_2,
      pos, grammar, root_key, family_root, pattern, stem per the spec's derivation table;
      blanks for the editor's fields. Flags disagreement when referring entries carry
      conflicting roots.
      → verify: hand-check three verbs against the shape of `akkamati 1` and `roseti`;
      confirm `-ati`/`-eti`/`-āti`/`-oti` all map to an existing template pattern.

- [x] Write `wanted_verbs.tsv`: verb, cst_count, sc_count, bjt_count, attested, referring
      entry count, referring lemmas, plus every derived field. All 664 rows.
      → verify: 189 rows attested; row count 664; spot-check `ruhati` 236x cst.

- [x] Write `x_queue.json` (attested verbs only, lemma → field dict, no `id`) under
      OUTPUT_DIR. Copy to gui2's path only under `--load-gui`.
      → verify: valid JSON, `Pass2XManager.load_data` accepts it without error.

- [x] Terminal summary: wanted count, attested per corpus, X-queue size.
      → verify: numbers reconcile with the TSV.


### Phase 1 verification (2026-08-26)

`uv run scripts/find/missing_pr_verbs.py` — 1.1s, clean. Counts match the spec's
established facts exactly: 664 wanted verbs, 862 dependent entries, 189 attested by
exact form (179 cst, 83 bjt, 38 sc), 475 unattested.

**Drift — a check the plan did not anticipate.** 15 of the 664 "verbs" carry no
present-tense ending, and inspection showed they are not present verbs at all:
`āyācituṃ` (inf), `saṃsīditvā` (abs), `paccuṭṭhātabba` (ptp), `santa`,
`uppajjamāna`, `pesiyamāna`, `ārabhiyamāno`, `ajjhabhavi`, `avahasi`, `niyojayi`,
`assāsesi`, `dammita`, `sāraddha`, `uddhata`, and one literal `??`. These are
grammar errors in the referring entries, not missing headwords. They are flagged in
the TSV as `not_a_pr_verb` and excluded from the X queue — 9 of them were attested
and would otherwise have been queued. X queue is therefore 180, not 189.

5 verbs have referring entries that disagree on the root (`chādayati`, `pahāpeti`,
`saṃvindati`, `vinibandhati`, `visajjati`); the majority value is used and the row
is flagged `root_disagreement`.

**Outputs:** `temp/missing_pr_verbs/wanted_verbs.tsv` (664 rows),
`temp/missing_pr_verbs/x_queue.json` (180). Loaded into
`gui2/data/pass2_x_words.json` with `--load-gui`; the file was `{}` beforehand, and
the flag refuses to overwrite a non-empty queue. Verified the written file passes
`Pass2XManager`'s own shape validation without consuming an entry.


### Field derivation revised (2026-08-26)

The editor asked for six more fields to be filled: root_sign, root_base,
family_compound, family_idioms, construction, and sanskrit. Each rule was measured
against the 3975 truly-plain present verbs already in the dictionary (excluding
causatives/passives, which `verb_type` detects from the grammar head as well as the
`verb` column). Five do not hold:

| rule | result |
|---|---|
| root_sign from the root record | 2789 match, 915 differ (~70%) |
| root_sign from the ending | `-ati` takes `a` only 67% of the time |
| construction = prefixes + base + ti | 3734 match, 1375 differ (66%) |
| construction, prefix-free only | 710 of 1176 (60%) — worse, compounds break it |
| sanskrit bracket = prefixes + sanskrit_root | 2264 of 3562 (64%) |
| sanskrit bracket, prefix-free only | 898 of 933 (96%) |
| family_compound = the word itself | 350 match, 3158 **empty**, 467 hold components |

Prefix sandhi is the cause: real entries spell it out ("ati > aty > acc + aya + ti")
and it cannot be reconstructed from the parts. `root_base` inherits `root_sign`'s
error rate because the sign is a component of the formula.

**Resolution — two field tiers, on the editor's instruction to use `_add`.**
`_click_x_button`'s no-id branch resolves any key against `dpd_fields.fields`, and
`dpd_fields.py:407` creates a `<name>_add` sibling for every config, so a queued key
of `root_sign_add` populates the proposal field with its transfer button.

- Real fields (certain): lemma_1, lemma_2, pos, grammar, root_key, family_root,
  stem, pattern.
- `_add` proposals: root_sign_add, root_base_add, construction_add, sanskrit_add,
  and meaning_1_add carrying every referring entry's pos and meaning — a past
  participle's meaning is the best available clue to its verb's.
- `family_compound` / `family_idioms`: left empty, matching the 3158/3975 majority.
- `root_base_add` is suppressed when the root carries several signs ("e, aya"),
  which would splice a list into the formula. 154 of 178 entries get one.
- `sanskrit_add` gives the bracket only; the inflected Sanskrit form in front of it
  needs verb formation and is left to the editor.

**Concurrent-tree note.** `dpd.db` changed mid-thread (commits landed that were not
present at session start): wanted verbs moved 664 -> 662 and dependent entries
862 -> 860, as two of the verbs were added as headwords by other work. Counts in the
spec's established-facts section reflect the earlier state.

**Queue reloaded** with 178 entries (187 attested, less 9 that carry no present-tense
ending). Written straight to `gui2/data/pass2_x_words.json` — the overwrite guard was
dropped on the editor's instruction to clear and refresh.

## Phase 2 — other inflected forms

- [ ] `build_paradigm(verb, pattern, db)` → `set[str]` of every inflected form the matching
      `inflection_templates` row generates for that stem.
      → verify: paradigm for a known verb (`gacchati`) contains `gacchanti`, `gaccheyya`;
      compare against that headword's stored `inflections`.

- [ ] `--paradigm` pass: for each phase-1 unattested verb, search all three corpora for any
      paradigm form; record the form found, which corpus, and its count.
      → verify: at least one of the 475 flips to attested; `russati` checked explicitly
      (0 hits as 3rd sg — does `russanti` occur?).

- [ ] Write `paradigm_attested.tsv` (verb, form_found, corpus, count, referring entries) and
      fold these verbs into the X queue.
      → verify: no verb appears in both the exact-form and paradigm attested sets.

- [ ] Update the terminal summary with paradigm hits.
      → verify: exact + paradigm + still-unattested = 664.

## Phase 3 — wide sweep

- [ ] Report-only scan: corpus forms matching basic present-tense endings that are absent
      from `lookup`, excluding the 664. Output a counted candidate list.
      → verify: run completes; candidate count and a sample reviewed with the user before
      any further work. Scope deliberately left open until phases 1 and 2 land.

## Open questions
- Homonym numbering: if an attested verb collides with an existing non-`pr` lemma, does the
  new verb take ` 1`/` 2`, or does the editor resolve it in gui2? Assumed the latter for now
  — the TSV flags the collision and leaves `lemma_1` bare.
- Phase 3's ending list and whether SYA should join the three corpora.
