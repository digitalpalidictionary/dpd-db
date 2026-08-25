# Plan: ati- prefix words → compounds, not root derivations

**Thread:** 20260823_ati_prefix_to_compound
**Spec:** `spec.md` in this folder
**Verified against the live `dpd.db` and the `justfile`:** 2026-08-23

## Deliverable

One new file: `scripts/fix/ati_prefix_to_compound.py`, following the shape of
its sibling `scripts/fix/variant_to_var_text.py` (module docstring explaining
the migration, `argparse`, `ProjectPaths`, `get_db_session`, `printer`,
`--dry-run`, idempotent, "CLOSE gui2 BEFORE RUNNING").

Its data file `scripts/fix/ati_prefix_to_compound.tsv` is written by the
script and edited by the user.

No new dependencies. Standard library `csv` with `delimiter="\t"`.

## Assumptions

1. The 90-row selection rule in the spec is the agreed scope.
2. The user edits the TSV in a spreadsheet or editor and saves it as TSV.
3. Editing the live `dpd.db` in place is the correct delivery mechanism; the
   change is persisted to git via `just backup`.
4. `family_compound` values are free text on the headword — the family tables
   are regenerated from them by the db build, so a new `ati garu` family needs
   no separate row to be created.
5. The user runs `just backup` and commits; the script never runs git.

## User decisions (resolved 2026-08-23 — no open questions remain)

1. **Frozen case forms use `abyayībhāva`.** Bare, not
   `kammadhāraya > abyayībhāva`.
2. **Compound-family token comes from the base word, looked up in the
   `family_compound` table.** That table is keyed by `compound_family` and
   confirms which token is real: `garu` (80), `ṭhāna` (152), `udaka` (180),
   `tulā` (5), `vipula` (17), `dūra` (13), `uṇha` (6), `sīta` (33) are all
   keys, and where a homonym digit is needed the table settles it (`matta2`
   and `dosa1` are keys, plain `matta`/`dosa` are not). The generator resolves
   the token as: the base's own `family_compound` if non-empty, otherwise the
   base's `lemma_clean`, and then checks the result against the table,
   flagging any token that is not a known key. The user double-checks every
   one by hand in the TSV.
3. **Irregular rows are left for the user** to settle row by row in the TSV.
   The generator marks them; it does not guess.

## Confidence

**8/10.** The convention is unambiguous and heavily evidenced in the data, the
four shapes all have working models already in the db, and the TSV round-trip
keeps every judgement call with the user. The point of risk is the phonetic
column on the `acc-` rows and the homonym digits — both are marked for review
rather than guessed.

---

## Phase 1 — Selection and shape classification

- [x] **1.1** Write the candidate query: root families beginning `ati `, minus
      any family containing a verb-form `pos`. Assert it returns 90 rows.
      → verify: row count is 90, and the 7 known verb-form singletons
      (`aticchati`, `atimodati`, `atisallekhati`, `atibyādippati`,
      `accādhāya`, `atikassa`, `atibandhitvā`) are absent.

- [x] **1.2** Classify each row into `plain` / `neg` / `case` / `abstr`,
      from `neg`, `pos`, and the `grammar` string
      (`... sg of ...` → case; `abstr` → abstr).
      → verify: print the counts per shape and eyeball against the 90-row dump
      in the spec.

- [x] **1.3** Implement base derivation (spec "Base derivation"), including
      un-gemination and `acc` + vowel coalescence, and the `base_ok` existence
      check against `lemma_clean`.
      → verify: `atiṭṭhāna` → `ṭhāna`, `accodaka` → `udaka`,
      `accukkaṭṭha` → `ukkaṭṭha`, `nātikisa` → `kisa`, `atinivāsa` → blank.

## Phase 2 — Proposal builder

- [x] **2.1** `grammar` rewriter: insert `comp` as the last qualifier, before
      `from`/`of`, and skip if `comp` is already present.
      → verify: `adj, from garu` → `adj, comp, from garu`;
      `ind, adv, acc sg of atisīta` → `ind, adv, comp, acc sg of atisīta`;
      `fem, abstr, from vepulla` → `fem, abstr, comp, from vepulla`.

- [x] **2.2** `family_compound` builder: `ati ` + base's own `family_compound`
      if non-empty, else base `lemma_clean` + homonym digit.
      → verify: `atitula` → `ati tulā`, `ativepullatā` → `ati vipula`,
      `atigaru` → `ati garu`.

- [x] **2.3** Per-shape construction / compound_construction / compound_type /
      derivative / suffix / phonetic builders, matching the four models named
      in the spec.
      → verify: regenerate the proposal for `atisīta`, `atitaruṇa`,
      `nātiucca`, `aticiraṃ` and `atijotitā` — words that are **already
      correct in the db** — and assert the proposal equals what is stored.
      This is the strongest available check that the builders are right.

- [x] **2.4** Mark rows needing review (`acc-` phonetic, homonym digit chosen,
      blank base, base not found) in a `review` column.
      → verify: the twelve rows named in the spec's "Rows that will need the
      user's eye" all carry a mark.

## Phase 3 — TSV round trip

- [x] **3.1** Generate mode: write the TSV — `do`, `id`, `lemma_1`, `shape`,
      `base`, `base_ok`, `review`, then `old_`/`new_` pairs for `grammar`,
      `derived_from`, `neg`, `root_key`, `root_sign`, `root_base`,
      `family_root`, `family_compound`, `construction`, `derivative`,
      `suffix`, `phonetic`, `compound_type`, `compound_construction`.
      Newlines inside `construction` written as `\n` escapes so every record
      stays on one physical line.
      → verify: 90 data rows, 34 columns, opens cleanly in a spreadsheet,
      round-trips through `csv` without loss.

- [ ] **3.2** Generate mode preserves an existing TSV's `do` and `base` edits
      and recomputes the `new_` columns from the edited `base`.
      → verify: hand-edit one `base`, regenerate, confirm the `new_` cells on
      that row followed and no other row moved.

- [x] **3.3** Apply mode: read the TSV, act on `do = y` rows only, write the
      `new_` values, commit once. `--dry-run` prints a per-row before/after
      table and commits nothing.
      → verify: `--dry-run` on the untouched TSV changes nothing
      (`git status` on `dpd.db` unchanged, row values re-queried and equal).

- [ ] **3.4** Apply mode refuses rows whose current db values no longer match
      the TSV's `old_` values, so a stale TSV cannot silently overwrite work
      done in gui2 in the meantime.
      → verify: change one field in the db by hand, re-run apply, confirm that
      row is reported as skipped and the rest still apply.

## Phase 4 — Real run

- [x] **4.1** Generate the TSV and hand it to the user for editing.
      → verify: report the shape counts and list the review-marked rows.

- [ ] **4.2** **HARD STOP.** User edits and approves the TSV. No db writes
      before this point.

- [ ] **4.3** Apply with `--dry-run`, show the user the summary, then apply
      for real.
      → verify: every approved id has empty `family_root` and `root_key`, a
      `family_compound` beginning `ati `, and a non-empty `compound_type`.

- [ ] **4.4** Re-run generate; confirm only the deliberately-declined rows
      remain.

## Deviations from the spec, found while implementing (2026-08-23)

The self-test in task 2.3 — rebuilding words that are already correct in the db
and diffing — caught four real bugs. All four are fixed and the test now
reproduces `atitaruṇa`, `atibahu`, `nātiucca`, `nātibahu`, `aticiraṃ` and
`atijotitā` exactly.

1. **The case ending cannot be recovered by comparing strings.** The accusative
   singular of `aticira` is written `cira + aṃ`, not `cira + ṃ`, because the
   ending replaces the stem-final vowel. It is now read from the last term of
   the old `construction`, which already holds it. A row whose old construction
   is empty (`accāsanne`) cannot be proposed at all and is blanked.
2. **`derived_from` is untrustworthy on case forms** — it variously holds the
   base (`kāla`), the joined form (`aticira`) or the inflected word itself
   (`kāle`, which was being taken as the base, yielding `ati + kāle + e`). It
   is now ignored for that shape; the base comes from stripping the lemma.
3. **The "is this base a verb" test was a string check** (`endswith("ti")`),
   which threw away the correct base `joti` for `atijotitā`. It now checks the
   candidate headword's actual `pos`.
4. **An `abstr` grammar without a `-tā`/`-tta` suffix is not the abstract
   shape.** `atiyācanā` was being forced into it, producing an empty suffix and
   a broken construction. It is now classified as plain.

Three additions beyond the spec, all of which earned their place:

- **A blocked-row concept.** A row that cannot be proposed (no base, or no
  recoverable case ending) is written with empty `new_*` cells and `do = n`
  rather than a half-built proposal the editor might approve by accident.
- **A base-root mismatch check.** If the base headword and the `ati-` word are
  built on different roots, the base is probably a lookalike rather than the
  real source. This caught `atidāyī` (`√dā` vs `√ḍi`) as the spec predicted,
  and three the spec had not: `atimatta 1`/`atimatta 2` (`√mā` vs `√mad`),
  `atipanna` (`√pat` vs `√pad`), and `nātikhīṇaṃ` (`√khī` vs `√tij`).
- **A `homonyms` column.** Reporting a homonym base as a *warning* flagged 83
  of 90 rows and buried the real findings, because most bases have homonyms and
  most need no digit. The count is now plain data in its own column.

## Mid-thread user corrections, applied 2026-08-25 (spec.md left as originally written)

Working from the printed TSV, the user gave five corrections beyond the
original spec. `spec.md`'s field table still lists these as unchanged/fixed —
recorded here rather than rewritten there, since the spec described the
initial design and these are approved deltas found in review:

1. **`pos`/`pattern` change for a pp/ptp headword.** Spec listed `pos` as
   unchanged. A pp/ptp used as a compound member is relabelled `adj` (matching
   the existing db convention on `sumanasikata`, a compound built on the pp
   `manasikata`), and `pattern`'s trailing pos token follows it. 12 of the 90
   words carried this.
2. **`compound_type` is always `kammadhāraya`**, or `kammadhāraya > abyayībhāva`
   for a frozen case form (indeclinable) — not bare `abyayībhāva` as the spec's
   9-of-11-majority guess had it.
3. **`compound_construction` is always `na + <surface>` or `ati + <surface>`**,
   one whole word, never decomposed into base + ending/suffix as the spec's
   per-shape formulas had it.
4. **`grammar` always names the base with `from <base>`** when one is known —
   including for a pp/ptp row, where it replaces the dropped `pp of X` clause,
   and even when the old grammar had no clause naming anything at all.
5. **Gemination bug found via review, not user correction**: `word.removeprefix("ati")`
   left a doubled leading consonant (`ati + ṭṭhāna`, `ati + kkhaya`) for a
   handful of `compound_construction` proposals. Fixed with a `strip_ati()`
   helper that undoes the sandhi when the base confirms it.

An independent post-apply review flagged two more points, both accepted by the
user as correct, not bugs:
- `nātikhīṇaṃ`'s `grammar` clause still names `atitikhiṇa`, the word's actual
  immediate prior form, not its `khīṇa`-based `derived_from` — the `grammar`
  case-clause records the last form a word was derived from, which is not
  always the same as the compound's own base. Left as-is.
- The `pos`/`pattern` relabelling (point 1 above) is confirmed intentional.

The three rows the tool could not propose (`accokaṭṭha`, `atibhārita`,
`accāsanne`) were fixed by the user directly, outside the script, after the
87-row apply. A `generate` re-run after those fixes finds 0 remaining
candidates — the migration is complete.

## Phase 5 — Gates

- [ ] **5.1** `uv run ruff check --fix`, `uv run ruff format`,
      `uv run pyright` on the new script; `just typecheck` repo-wide.

- [ ] **5.2** Run `db_tests` and compare against a baseline taken **before**
      Phase 4.3, so any pre-existing failures are not attributed here.
      → verify: no new failure naming any of the 90 lemmas.

- [ ] **5.3** `just backup` to write the change into `db/backup_tsv/`.

- [ ] **5.4** Report the changed files and propose a commit message. **Do not
      run git** — the user commits.

## Baseline to capture before Phase 4.3

- `db_tests` current output, so new failures are distinguishable.
- A copy of `dpd.db` outside the repo, as a rollback for a bulk write.
