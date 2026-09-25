# Spec: missing present-tense verbs

## GitHub issue
#266 — Grammar: resolve all verbal forms to a present tense or root

## Overview
Find present-tense verbs that the texts attest but the dictionary lacks, fill in what
follows mechanically, and hand them to the editor for manual completion through the
pass2add X button. Three phases, narrowest first.

Grew out of `20260512_verb_finder`: derived forms name a present verb in their
`grammar`, and when that verb has no headword the entry is dangling. `verb_finder`
decides whether to rewrite such an entry to a root; this thread decides whether the
verb should instead be added.

## Established facts (2026-09-21, after the grammar fix landed)
- 257 referenced-but-missing verbs remain, named by 303 derived-form entries with a
  `meaning_1`. Before `verb_grammar_fixer` applied its 368 corrections it was 662
  verbs / 860 entries — resolving those entries to roots removed most of the
  dangling references.
- Corpus word frequencies exist as JSON, no XML parsing needed: `cst_freq.json`
  (975,613 forms), `bjt_freq.json` (500,251), `sc_freq.json` (169,419).
- Four present patterns cover 5632 of 5818 present verbs: `ati pr`, `eti pr`,
  `āti pr`, `oti pr`. All exist in `inflection_templates`, so real paradigms are
  generated rather than guessed. **89 present headwords end in none of the four**
  (`atthi`, `bravīti`, `asmi`), so the ending test is a heuristic, not a definition.
- The X button (`gui2/pass2_x_manager.py`) reads `pass2_x_words_path`, a gitignored
  JSON mapping lemma → field dict; no `id` means a new word. It archives every entry
  it hands over to `pass2_x_words_done_path`.
- `pass2_add_view._click_x_button`'s no-id branch resolves any key against
  `dpd_fields.fields`, and `dpd_fields.py:407` creates a `<name>_add` sibling for
  every config — so a queued `root_sign_add` lands in the proposal field.

## Queue shape
The editor works the queue in pass2add **with the pass1-field filter on**, so the
queue carries only `gui2.dpd_fields_lists.PASS1_FIELDS` and their `_add` siblings.
Anything outside that list is invisible there and is not emitted.

Real values (certain): `lemma_1`, `lemma_2`, `pos`, `grammar`, `root_key`,
`family_root`, `stem`, `pattern`.

`_add` proposals (the editor accepts or rejects): `meaning_2_add` — pass1 shows
meaning_2, not meaning_1 — plus `root_sign_add`, `root_base_add`,
`construction_add`.

`comment` carries the provenance: the form actually found, its grammar label, corpus
and count; the root meaning; and the entries whose grammar names this verb.

Not emitted: `sanskrit` (outside PASS1_FIELDS), `family_compound` (3158 of 3975 plain
present verbs leave it blank).

## Why the derivations are proposals, not values
Measured against the 3975 truly-plain present verbs in the dictionary:

| rule | accuracy |
|---|---|
| root_sign from the root record | 2789 / 3704 (~70%) |
| construction = prefixes + base + ti | 3734 / 5109 (66%) |
| sanskrit bracket = prefixes + sanskrit_root | 2264 / 3562 (64%) |
| sanskrit bracket, prefix-free only | 898 / 933 (96%) |

Prefix sandhi is the cause — real entries spell it out
("ati > aty > acc + aya + ti") and it cannot be reconstructed from the parts.
`root_base` inherits `root_sign`'s error rate because the sign is part of the formula.

## Already-declined verbs
Anything the X button has archived that is still not a present headword was a
deliberate no. Those are excluded on every run. This is derived from the done file,
not a hand-maintained list; it identified the editor's 19 rejections exactly.

## Phases
1. **Exact form.** Attest each wanted verb against CST, SC and BJT by its plain form.
   DONE — 178 queued, 159 added by the editor.
2. **Other inflected forms.** Generate the full present paradigm from the matching
   `inflection_templates` pattern and re-attest. A generated form that another
   headword already owns in `lookup` is skipped as a collision. DONE — 77 found.
3. **Wide sweep.** DROPPED on 2026-09-22. Adding every obscure verbal form that occurs
   only in late commentaries is a side quest, not part of #266. See the addendum.
4. **Maintenance.** A standing check keeps verbal forms in sync as verbs are added or
   removed. DONE — see the addendum.

## Constraints
- Read-only against `dpd.db`. No headwords are created by script.
- Attestation is exact-form matching over the frequency JSONs. A corpus hit proves the
  string occurs, not that it is a present verb — the evidence travels in the comment
  so the editor can judge.
- Modern type hints, `Path` from pathlib, `tools.printer`, `tools.db_helpers`.
- Output under `temp/missing_pr_verbs/`, except the queue, which is copied to the
  path gui2 reads only under `--load-gui`.

## What's not included
- No writes to `dpd.db` from this script. No automatic headword creation.
- No meaning, construction or root analysis presented as fact.
- The 15 wanted forms with no present-tense ending are flagged `not_a_pr_verb` and
  excluded from the queue. They are not missing verbs: 5 are entries whose grammar
  names themselves, 7 are negatives correctly built on a participle, 2 name an
  aorist, 1 is literally `??`. Handling those is a separate job.

---

# Addendum: closing #266 with a maintenance test (2026-09-22)

## Decision
The one-off clean-up is finished. What stays behind is a standing check that keeps
verbal forms in sync as the dictionary changes. Adding every obscure verbal form
that appears only in late commentaries is explicitly **out of scope** — a side quest,
not part of this issue.

## The rule being maintained
A derived form's `grammar` names the present verb it comes from when that verb is a
headword, and the prefixes plus root when it is not. That is the whole rule. It is
already enforced once by `verb_grammar_fixer`; the maintenance test enforces it
continuously.

## What the test does
`db_tests/single/test_verb_grammar_sync.py`, run like its siblings.

1. Recomputes every derived form's correct `grammar` from the live database.
2. Applies the unambiguous changes and prints each one.
3. Lists the ambiguous cases for the editor.
4. Remembers ambiguous cases the editor has dismissed, in
   `db_tests/single/test_verb_grammar_sync.json`, so a judged case stays judged.

This catches both directions the editor asked about:
- A present verb is **added** → entries pointing at its root now resolve to the verb.
- A present verb is **deleted** → entries pointing at it now resolve to the root.

## Reuse, not duplication
The test imports `build_pr_verb_index`, `scan_derived_forms`, `load_cst_word_freq`
and `load_all_lemmas` from `verb_finder`, and the write path from
`verb_grammar_fixer`. No rule is restated in a second place. A change to the rule
therefore changes one file, not two.

## Safety
- The test writes to `dpd.db`, which is what the editor asked for. Every change is
  printed as "before → after" so the run is auditable.
- `--dry-run` reports without writing.
- Each row's current grammar is re-checked immediately before writing, so a value
  changed since the scan is skipped rather than overwritten.
- gui2 must be closed, as with every script that writes to the database.

## Not included
- No new headwords are created. A verb the corpus attests but the dictionary lacks is
  still the finder's job, run by hand when the editor wants a batch.
- Phase 3, the wide corpus sweep, is dropped from this issue. It is the side quest the
  editor has ruled out.
- The other buckets (ambiguous, rootless, field disagreements, malformed grammar)
  remain reported, not auto-fixed.

---

# Addendum 2: the rule covers present verbs too (2026-09-22)

## What was missed
The rule is "a verbal form names the present verb it comes from when that verb is a
headword, and the prefixes plus root when it is not". It was implemented for derived
forms only — participles, absolutives, aorists and the rest.

A present verb's own grammar also names a verb. `anussāveti` reads "pr, caus of
anusuṇāti", and `anusuṇāti` is not in the dictionary. Nothing checked that, because
the scan queried only the derived parts of speech. The editor found it.

## What now happens
`scan_present_verbs` reads every present verb with a meaning whose grammar carries a
`caus`, `pass`, `intens` or `desid` marker. Where the named verb is not a present
headword and a family root exists, the grammar is repointed at the root.

135 entries qualify: 100 causatives, 33 passives, 2 desideratives.

## Denominatives and impersonals are excluded
A denominative is built from a NOUN, so naming a noun is correct. Same for an
impersonal. A grammar carrying `deno` or `impers` is left alone **even when it also
carries a marker from the list above** — `nimmādeti` is "pr, caus, deno of nimmada",
and `nimmada` is the noun it comes from. The first attempt at this change did not
make that exclusion and would have corrupted that entry.

## One rule, three callers
`verb_finder`, `verb_grammar_fixer` and the maintenance script all call the same two
scan functions. None can drift from the others.

---

# Addendum 3: present verbs resolved like participles (2026-09-25)

`scan_present_verbs` now takes the corpus frequencies and the candidate index, and
resolves a causative, passive or desiderative whose named source is missing in this
order:

1. The corpus attests the missing verb → reported as "needs verb added", never written.
2. Any plain verb exists at the same family root and root key → the editor decides,
   even when there is only one.
3. Nothing at that root → repointed to the root family.

Point 2 deliberately differs from participles, where a single candidate is written
automatically. For a causative the lone candidate was wrong in both real cases tested:
removing `abhivadati` left only `nabhivadati`, a negative verb whose grammar is a bare
"pr"; removing `uppajjati` left only `vuppajjati`, a variant spelling.

Causatives are recognised by four signals: the `verb` column; the grammar head,
including a truncated "pr, caus of"; `meaning_lit` containing "caus"; and the root sign,
where `*āpe` and `*āpaya` are always causative and `*e` and `*aya` are causative except
on a group 8 root.

Candidate lists show homonym numbers so the editor can see which verb is on offer. The
grammar field never receives one.

The maintenance script pauses after each stage and offers exception, add, root family,
pass, and quit for each undecided entry.
