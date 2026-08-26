# Spec: missing present-tense verbs

## GitHub issue
(none provided)

## Overview
Find present-tense verbs that the texts attest but the dictionary lacks, fill in every
field that can be derived mechanically, and hand them to the editor for manual
completion through the pass2add X button. Three phases, narrowest first.

Grew out of `20260512_verb_finder`: 664 present verbs are named in the `grammar` of
existing derived forms (862 entries depend on them) but have no `pos='pr'` headword.
`verb_finder`'s `verb_in_cst` bucket holds back the subset of those whose entries would
otherwise have their grammar rewritten to a root — adding the verb is the better fix.

## Established facts
- 4486 distinct present verbs exist as headwords (5818 rows incl. homonyms).
- 664 referenced-but-missing verbs, referenced by 862 derived-form entries with a
  `meaning_1`. Exact-form attestation: 97 CST-only, 48 BJT+CST, 28 all three, 6 BJT-only,
  6 CST+SC, 3 SC-only, 1 BJT+SC — 475 unattested in their 3rd-singular form.
- Corpus word frequencies already exist as JSON, no XML parsing needed:
  `cst_freq.json` (975,613 forms), `bjt_freq.json` (500,251), `sc_freq.json` (169,419).
  Per-file variants (`*_file_freq.json`) give book-level location.
- 5632 of 5818 present verbs use four patterns: `ati pr` (3694), `eti pr` (1656),
  `āti pr` (282), `oti pr` (101). All four exist in `inflection_templates`, so real
  paradigms can be generated rather than guessed endings.
- The X button (`gui2/pass2_x_manager.py`) reads `pass2_x_words_path`, a gitignored JSON
  mapping lemma → field dict. An entry without an `id` is a new word. The file is swapped
  per batch and is explicitly not covered by tests.

## Field derivation
Mechanically derivable for a new present verb:
- `lemma_1` — the attested verb form (homonym number appended only on collision)
- `lemma_2` — `lemma_1` without the homonym number
- `pos` — `pr`
- `grammar` — `pr`
- `root_key`, `family_root` — carried over from the derived-form entries that name it
- `pattern` — by ending: `-ati`/`-eti`/`-āti`/`-oti`
- `stem` — `lemma_2` minus the pattern's ending

Left blank for the editor: `meaning_1`, `meaning_lit`, `construction`, `root_sign`,
`root_base`, `trans`. These need lexicographic judgement and must not be guessed.

## Phases
1. **The 664, exact form.** Attest each against CST, SC and BJT by its plain form. Emit a
   TSV (all 664, attested or not, with per-corpus counts) and an X-queue JSON for the
   attested ones.
2. **Other inflected forms.** For the phase-1 unattested verbs, generate the full present
   paradigm from the matching `inflection_templates` pattern and re-attest. A verb found
   only as e.g. `-nti` or `-eyya` still needs adding. Records which form was found.
3. **Wide sweep.** Scan all three corpora for basic inflected verbal forms absent from the
   dictionary's `lookup`, beyond the 664 already referenced. Report only — scope and
   output format to be settled after phases 1 and 2 land.

## Constraints
- Read-only against `dpd.db`. No headwords are created by script; the editor adds them
  through gui2.
- Attestation counts come from the frequency JSONs, exact-form matching only. A corpus hit
  proves the string occurs, not that it is a present verb — the TSV must carry the
  evidence so the editor can judge.
- Modern type hints, `Path` from pathlib, `tools.printer` for output,
  `tools.db_helpers.get_db_session`. No `sys.path` hacks.
- Output under `temp/missing_pr_verbs/`, except the X-queue JSON which goes to the path
  gui2 reads.

## How we'll know it's done
- Phase 1: TSV lists all 664 with per-corpus counts; 189 attested by exact form; X JSON
  loads in gui2 and the first entry populates pass2add's fields.
- Phase 2: every phase-1 unattested verb has been searched across its full generated
  paradigm; the report names the inflected form that attested each new find.
- Phase 3: a report of candidate verbal forms absent from `lookup`, with counts.

## What's not included
- No writes to `dpd.db`. No automatic headword creation. No changes to `verb_finder` or its
  grammar-rewrite proposals — the 116 entries it parks stay parked until the editor adds
  the verbs.
- No meaning, construction or root analysis generated for any verb.
