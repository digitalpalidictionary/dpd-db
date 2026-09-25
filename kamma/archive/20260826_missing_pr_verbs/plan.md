# Plan: missing present-tense verbs

Issue #266 — Grammar: resolve all verbal forms to a present tense or root.

## Architecture Decisions
- **`scripts/find/missing_pr_verbs.py` owns the whole finder.** Phase 2 became an
  extra search pass inside it rather than a flag or a second script — one code path
  is simpler than an option nobody would leave off.
- **Reuse `verb_finder`'s parser.** `parse_grammar`, `lemma_clean`, `DERIVED_POS` and
  `write_tsv` already handle the grammar conventions against the live db.
- **Reuse `inflection_templates`.** Real stem/ending grids, not hand-rolled endings.
- **The queue is written to gui2's path only under `--load-gui`.**

## Phase 1 — exact form — DONE

- [x] `scripts/find/missing_pr_verbs.py` skeleton, output under
      `temp/missing_pr_verbs/`.
- [x] `collect_wanted_verbs(db)` — each referenced-but-missing verb mapped to the
      entries naming it. Skips root references, multi-word targets, bare `na`/`no`.
- [x] `load_corpus_freq(pth)` — cst / sc / bjt totals from the `*_freq.json` files.
- [x] `derive_certain` / `derive_proposals` — the two field tiers.
- [x] `wanted_verbs.tsv` — every wanted verb with per-corpus counts and derivations.
- [x] `x_queue.json`, copied to gui2 under `--load-gui`.
- [x] Terminal summary reconciling with the TSV.

**Outcome.** 178 queued on 2026-08-26; the editor added 159 and declined 19.

**Drift.** 15 wanted forms carry no present-tense ending and are not present verbs
(`āyācituṃ` inf, `saṃsīditvā` abs, `santa`, one literal `??`). Flagged
`not_a_pr_verb`, excluded from the queue. Note the ending test is a heuristic: 89
real present headwords also fail it.

## Phase 2 — other inflected forms — DONE

- [x] `build_paradigm(stem, pattern, templates)` from the real template grid.
      → verified against stored data: `gacchati 1`, `bhavati 1` and `roseti`
      reproduce their `inflections_list` exactly (57/57, 57/57, 51/51).
- [x] Paradigm search for every verb the exact-form check missed, recording the
      form found, its grammar label, corpus and count.
- [x] `paradigm_attested.tsv`, and these verbs folded into the queue.
- [x] Summary updated.

**Outcome.** 77 verbs found by another form — 17 as 3rd plural, 14 as 2nd singular
imperative, 13 as 2nd singular, 8 as 3rd singular optative.

**Drift.** Two changes from the plan as written:
1. No `--paradigm` flag; the pass always runs.
2. **Collision filter added.** A generated form already owned by another headword in
   `lookup` is skipped — without it the pass manufactures verbs from unrelated words.

**Evidence is thinner than phase 1.** 43 of the 77 rest on a single corpus
occurrence; 44 were found in more than one form. Two hits are on forms of five
characters or fewer (`kutha`, `tima`).

## Queue reshaped for pass2add + pass1 filter (2026-09-21) — DONE

The editor works the queue in pass2add with the pass1-field filter on. Changes:

- [x] Emit only `PASS1_FIELDS` and their `_add` siblings; drop everything else
      (`sanskrit` is outside the list and is no longer emitted).
- [x] `meaning_1_add` → `meaning_2_add`: pass1 shows meaning_2.
- [x] `comment` carries provenance — the form found, its label, corpus and count;
      the root meaning; and the entries whose grammar names this verb.
- [x] `load_already_seen(db)` excludes anything the X button has archived that is
      still not a present headword. Derived from the done file, not hand-maintained;
      it matched the editor's 19 rejections exactly.

**Outcome.** 50 entries, loaded into `gui2/data/pass2_x_words.json`. Down from 96:
19 declined, and the rest resolved when `verb_grammar_fixer` applied its 368
corrections — wanted verbs fell from 662 to 257.

**Known gap.** 15 of the 50 end `-āpeti` / `-āpayati`, which reads causative, but
`grammar` is set to plain "pr" for all of them. No evidence either way is available
to the script; the editor corrects these in gui2.

## Phase 3 — wide sweep — DROPPED

The editor ruled this out on 2026-09-22. Adding every obscure verbal form that occurs
only in late commentaries is a side quest, not part of #266.

## Phase 4 — maintenance test — DONE

Keep the dictionary's verbal forms in sync from now on. A db_test is a maintenance
script that keeps the data in order, so this one writes its fixes.

- [x] Register the exceptions file in `ProjectPaths`, next to its siblings.
      → verify: the path resolves and the siblings' naming style is matched.

- [x] `db_tests/single/test_verb_grammar_sync.py`. Recompute every derived form's
      correct grammar from the live db, reusing `verb_finder`'s index, scan, CST
      frequencies and all-headword set. No rule restated in a second place.
      → verify: on the current db it finds nothing to change, because
      `verb_grammar_fixer` already applied all 368.

- [x] Apply the unambiguous changes, printing each as before → after. Re-check each
      row's current grammar immediately before writing.
      → verify: delete a present verb in a throwaway copy of the db, run the test,
      confirm the entries that named it move to the root. Restore the copy.

- [x] Report ambiguous cases, with an exceptions file so a dismissed case stays
      dismissed.
      → verify: dismiss one, re-run, confirm it does not reappear.

- [x] `--dry-run` reports without writing.
      → verify: run it on the live db and confirm nothing changes.

- [x] Add a justfile recipe alongside the other single-test recipes.
      → verify: the recipe runs.


### Phase 4 verification (2026-09-22)

**On the live db the script finds nothing to change.** That is the expected result:
the one-off fixer already applied all 368. It lists 53 cases where more than one verb
fits, which it never guesses.

**Both directions proven against the live db inside a transaction that was rolled
back.** The db was never written.

- Verb removed. `onandhati`'s pos was changed away from `pr`. The script then moved
  all 4 entries that named it to the root: `avanaddha`, `onaddha`, `onaddhitvā`,
  `onandhitvā` → "pp/abs of ava √nadh". Rolled back; `onandhati` is still `pr`.
- Verb added. A present verb was inserted at `√bah`, which had none. The script moved
  both entries naming that root onto the new verb, negative included:
  "pp of √bah" → "pp of testverbati", "pp of na √bah" → "pp of na testverbati".
  Rolled back; the test verb is not in the db.

A real row delete is refused by the ORM because `family_root` depends on the row, so
removal was simulated by changing the pos. The rule reads pos, so this exercises the
same path.

**Bug found by that test, and fixed.** The any-pos guard added on 2026-09-21 made the
script inert in the removal case: a verb that stops being `pr` is still a headword, so
the guard left every entry naming it alone. The guard is now narrowed to the case it
was written for:

- The grammar names the entry itself → left alone, reported as a data error. Covers
  `āyācituṃ` and `saṃsīditvā 1`.
- The grammar carries "na" and names a headword of another pos → left alone. This is
  a negative built on a participle: `anuddhata` is "pp of na uddhata". Covers
  `anuddhata` 1 and 2 and `asāraddha`.
- Anything else re-resolves, which is what catches a removed verb.

All five originally protected entries are still left alone. The live run reporting
zero changes is the proof.

**Not written to the temp directory.** The script's only file is its exceptions list,
which sits beside it. Everything else goes to the terminal.

**Rule logic is not duplicated.** The script imports the index, the scan, the corpus
frequencies and the all-headword set from the finder. Restating the rule in a second
place is what caused the fixer to drift from the finder on 2026-09-21.

## Backlog — raised, not actioned
- The 15 `not_a_pr_verb` forms: 5 entries whose grammar names themselves, 7
  negatives correctly built on a participle, 2 naming an aorist, 1 `??`.
- Whether missing **aorist** headwords deserve their own category — the present
  paradigm generates every form except the aorist.
- `verb_finder`'s remaining buckets: 58 ambiguous, 57 rootless, 44
  grammar/derived_from disagreements, 10 malformed grammar strings.

## Unverified assumptions in the current code
Named so they are not mistaken for verified behaviour:
- A present verb ends `-ati`/`-eti`/`-āti`/`-oti`. 89 headwords do not.
- 65 multi-word grammar targets are all compound verbs and are skipped. Some are
  prefixed roots written without the √ (`ajjhappatta`: "pp of adhi ā pat").
- Majority wins when referring entries disagree about the root (4 cases).
- `lookup` is complete and current — phase 2's collision filter depends on it.
- The corpus frequency files hold clean word forms.
- `no` as a negation particle and homonym numbers in grammar targets: both matched
  zero rows when measured. The handling is dead code.

## Phase 5 — the rule extended to present verbs (2026-09-22) — DONE

- [x] `scan_present_verbs` in `verb_finder`, with its own grammar parser.
      `parse_grammar` cannot read "pr, caus of X": it expects the pos alone before
      " of ", and here the marker sits between them.
      → verify: 135 corrections, 100 caus, 33 pass, 2 desid.

- [x] Exclude `deno` and `impers` even when another marker is also present.
      → verify: `nimmādeti` ("pr, caus, deno of nimmada") is no longer proposed.

- [x] Wire the new group into the fixer and the maintenance script, so all three
      callers read one rule.
      → verify: all three report the same group.

- [x] Soundness check over all 135: no no-ops, every proposal keeps its marker and
      gains a root sign, negation preserved in all 4 cases that carry it, trailing
      text preserved.

- [x] Justfile: writing is the default recipe, dry run is the named one.

### What went wrong, recorded so it is not repeated

**1. The proof was shaped to pass.** The removal half of the rule was proven with
`onandhati`, whose corpus frequency is 0. That is the only shape of verb for which the
code worked. With a corpus-attested verb — `gacchati`, 5244 occurrences — 47 entries
were stranded and the run printed a success line. An independent reviewer found it.
A proof that picks its own fixture proves nothing.

**2. The rule was applied to one group out of three.** Derived forms were handled;
present verbs and special derived forms were never scanned. The script's whole purpose
is to notice when a verb changes, and a causative naming a deleted verb is exactly
that case. The editor found it, not the review.

**3. A "draft verb" category was invented.** Entries without a meaning were excluded
as redirect targets on the grounds that they were unfinished. They are ordinary
headwords. The filter and the citation machinery built on top of it were both removed.

**4. A guard was written from spelling instead of evidence.** Candidates beginning
"na" were rejected as doubled negatives. 244 present headwords begin that way and 84
are ordinary verbs. The real signal is the grammar field, which says "from na X"
outright. The guard was removed and replaced with that test.

**5. The guard for negatives built on a participle made the script inert.** Leaving an
entry alone whenever its named source was a headword of any pos also covered the case
where a verb changed pos, which is the case the sync script exists for. Narrowed to
self-references and to grammars carrying "na".

The common thread: each was a rule inferred from one example and never measured
against the data before being written into code.

## Phase 6 — editor's test round and re-review fixes (2026-09-23 to 2026-09-25) — DONE

- [x] Stage pauses after each group of output.
- [x] Undecided prompt: (e)xception, (a)dd, (r)oot family, Enter, (q)uit, coloured.
- [x] Candidates shown with homonym numbers, written without; root and root key shown.
- [x] Causative detection widened to four signals: verb column, grammar head (split on
      " of" as a word, catching 145 truncated "pr, caus of" grammars), `meaning_lit`
      (54 more), root sign (9 from `*āpe`/`*āpaya`, 103 from `*e`/`*aya` outside group 8).
- [x] Summary label shortened to fit the printer's 20-character column.
- [x] `scan_present_verbs` given the corpus check and the candidate lookup that
      `scan_derived_forms` already had (re-review findings 1 and 2).
      → verify: removing `uppajjati` (18,171 corpus hits) now reports its two
      causatives as needing the verb added; before, both were silently rooted.

### Mistake recorded

**6. The present-verb scan repeated the first blocking bug.** It was written to close
the "present verbs never scanned" finding, and it omitted the corpus check that the
derived-form scan had been given for exactly that failure. A removed, corpus-attested
source verb would have been silently rooted. The fix for one group was not carried to
the next group built on the same rule.

**7. A database timestamp was used as proof of no writes.** `dpd.db` runs in WAL mode,
so writes land in the log file and the main file's mtime does not move. Data must be
read to confirm state.
