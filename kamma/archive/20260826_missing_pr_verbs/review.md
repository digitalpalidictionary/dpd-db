## Thread
- **ID:** 20260826_missing_pr_verbs
- **Objective:** Resolve every verbal form to a present verb or a root (#266), and leave a maintenance script that keeps them in sync.

## Files Changed
- `scripts/fix/verb_finder.py` — verb-type and fused-negative filters; self-reference and negative-on-a-participle branches; rootless, data_errors and verb_in_cst groups.
- `scripts/fix/verb_grammar_fixer.py` — applies the unambiguous corrections; split diff files; `--only`; now reports entries deleted since the scan.
- `scripts/find/missing_pr_verbs.py` — finds verbs the texts attest but the dictionary lacks; paradigm search; queue shaped for pass2add under the pass1 filter.
- `db_tests/single/test_verb_grammar_sync.py` — NEW. The standing maintenance script.
- `db_tests/single/test_verb_grammar_sync.json` — NEW. Dismissal list.
- `tools/paths.py` — one path entry for that list.
- `justfile` — two recipes, one read-only and one that writes.

## Findings
Independent reviewer, own context, plus CodeRabbit. 13 findings.

| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | blocking | sync script + `verb_finder` | Removing a verb the corpus attests produced no change and no report, while printing a success line. Reproduced: remove `gacchati` → 47 entries stranded. The original proof used `onandhati`, corpus frequency 0 — the one case that hides it. | The removal half of the issue was inert for nearly every real verb. | Report `verb_in_cst` as its own group: the verb is gone but the texts have it, so re-add the verb. |
| 2 | major | sync script | `apply_changes` was copied from the fixer, though the spec said it was imported. | Restating logic in two places is what made the fixer drift from the finder on 2026-09-21. | Import it from the fixer. |
| 3 | minor | `justfile` | The recipe wrote to the database with no flag, unlike its sibling. | A casual run edits grammar unprompted. | Read-only recipe by default, a second one to write. |
| 4 | minor | sync script | End of input broke the loop, so a piped run showed 1 case of 53 while the summary said 53. | Comment stated the opposite of the behaviour. | Keep listing, stop asking. |
| 5 | minor | sync script | The closing counts did not match what the run did. | The audit line disagreed with the output. | Count what was written and what is still undecided. |
| 6 | minor | fixer | A row deleted since the scan was silently absent. | Indistinguishable from a written row. | Report it. |
| 7 | minor | sync script | The docstring promised protection against a concurrent writer that the code does not give. | Over-promise. | Claim removed. |
| 8 | nit | sync script | Unused dataclass field. | Dead code. | Dataclass replaced by plain rows. |
| 9 | nit | `missing_pr_verbs` | `CERTAIN_FIELDS` unused, superseded. | Dead constant. | Deleted. |
| 10 | nit | `verb_finder` | Comment said "244 ordinary verbs begin na". Re-measured: 244 is every present headword starting those letters; 84 are ordinary verbs. | A wrong number in a comment reads as fact. | Wording corrected with both figures. |
| 11 | nit | dismissal list | Shipped as `[]` while the loader wants a mapping, so a hand edit would be silently discarded. | Silent data loss. | Ships as `{}`. |
| 12 | nit | sync script | `list[dict]` unparameterised. | Project asks for specific hints. | `list[dict[str, str]]`. |
| 13 | note | two dirty files | `db_tests_columns.tsv` and `pass2_exceptions.json` belong to another session. | Staging by directory would sweep their work. | Excluded from staging. |

CodeRabbit raised one further point: the spec called the wide sweep "not started" in one place and "dropped" in another. Corrected.

## Fixes Applied
All 13 fixed, plus the CodeRabbit point. The editor also asked for the prompt to be rebuilt: it now offers exception, add, pass and quit, with the candidate verbs numbered so one can be picked directly. Every `print` call was replaced with the shared printer helper.

## Test Evidence
- `ruff check` and `ruff format --check` (scope: all 5 changed Python files) → pass.
- `pyright` (scope: all 5 changed Python files) → 0 errors, 0 warnings.
- `just typecheck` (scope: whole repo, pyrefly, ~390 files) → 0 errors.
- Removal case, with a corpus-attested verb (scope: `gacchati` 5244x and `chindati` 268x, in memory, nothing written) → 47 and 41 entries now reported as needing the verb back. Before the fix, 0 reported.
- Removal case, unattested verb (scope: `onandhati`, rolled back) → 4 entries repointed to the root.
- Addition case (scope: one synthetic verb at `√bah`, rolled back) → 2 entries repointed, negative included.
- Protected entries (scope: all 5 originally at risk) → `anuddhata` 1 and 2 and `asāraddha` hit the negative branch; `āyācituṃ` and `saṃsīditvā 1` hit the self-reference branch. All left alone.
- Live dry run (scope: whole db, 10130 derived forms) → 0 to repoint, 9 needing the verb back, 53 undecided.
- Database state after all probes (scope: the 6 rows any probe touched, plus headword count) → identical to before.

## Not Verified
- The 368 corrections applied on 2026-09-21 were sampled by the editor, not re-checked one by one. They are already in the database and cannot be reconstructed.
- The accuracy figures quoted in the spec (70%, 66%, 64%, 96%) were measured once, in August, and not re-measured.
- The corpus-attestation path of `missing_pr_verbs.py` and its `--load-gui` branch were not re-run in this review.
- Whether the 53 undecided candidate lists are lexicographically sound. That is the editor's judgement, and the script never guesses them.
- One data issue noticed, not this thread's: `dassāpeti` appears as a plain candidate because its grammar is bare "pr" with an empty verb column, though its form is causative. Harmless here, since undecided cases are never applied automatically.

## Verdict
PASSED
- Review date: 2026-09-22
- Reviewer: independent agent with its own context, plus CodeRabbit; fixes and re-verification by the implementing agent.

---

## Re-review needed (2026-09-22, later the same day)

**The PASSED verdict above is superseded.** It was written before the rule was
extended to present verbs. It does not cover what is now in the tree.

### Found by the editor after that verdict

| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 14 | blocking | `verb_finder` | The rule was never applied to present verbs. A causative whose own grammar names a deleted verb was invisible: `anussāveti` reads "pr, caus of anusuṇāti" and that verb is not in the dictionary. 135 entries affected. | The script exists to notice when a verb changes. A causative naming a gone verb is that exact case. Two of three groups were unscanned. | `scan_present_verbs`, wired into all three callers. |
| 15 | major | `scan_present_verbs`, first attempt | Denominatives carrying a causative marker were included. `nimmādeti` is "pr, caus, deno of nimmada"; the noun is the correct source. | Would have corrupted a correct entry. | Exclude `deno` and `impers` even alongside another marker. |
| 16 | minor | `justfile` | Writing had been made the non-default recipe on the reviewer's advice. The editor wants writing by default. | The script is a maintenance script; it is meant to write. | `test-verb-grammar` writes, `test-verb-grammar-dry-run` does not. |

### Coverage of the new work
- 135 corrections checked in full: no no-ops; every one keeps its marker and gains a
  root sign; negation preserved in all 4 cases that carry it; trailing text preserved.
- `ruff check`, `ruff format --check`, `pyright` (scope: all changed files) → pass.
- Dry run on the live db → 135 to repoint, 9 needing the verb back, 48 undecided.
- NOT verified: the 135 have not been read one by one for lexicographic sense. The
  editor is reviewing them over a day before applying.
- NOT verified: no independent reviewer has seen the present-verb work. The verdict
  above predates it.

### Note on the database
The editor ran the script interactively to test it. Four dismissals are on file and
one entry was repointed with the add option. That is their own change, not a stray
write from this session.

## Verdict
BLOCKED pending re-review — the present-verb work has had no independent review, and
the editor is reading the 135 corrections before deciding whether to apply them.
- Date: 2026-09-22
- Next step: re-run `/kamma:3-review` once the editor has decided on the 135.

---

## Re-review (2026-09-25)

Independent reviewer on Sonnet, own context. CodeRabbit attempted under both
organisations: "digitalpalidictionary" refused with 403 "not a member of the requested
organization" (no seat assigned); "bdhrs" failed twice with "Connection failed:
WebSocket closed". Recorded as unavailable.

| # | Severity | Location | What | Fix |
|---|----------|----------|------|-----|
| 17 | blocking | `verb_finder.scan_present_verbs` | No corpus check. Removing `uppajjati` (18,171 hits) silently rooted `uppādeti` and `uppādayati`. Same bug as finding 1, in the newest code. | Corpus-attested missing source → "needs verb added", never written. |
| 18 | major | same | No same-root candidate lookup; a missing source always went to the root. | Candidates are now looked up — but any candidate sends the entry to the editor, not to an automatic write. The reviewer recommended writing a single candidate; both real cases showed the lone candidate is wrong (`nabhivadati`, `vuppajjati`). |
| 19 | nit | `verb_finder` comment | Stated counts drift with the data (now 245 / 85). | Dated the figures. |

### Test evidence
- Reviewer's case 1, in memory: removing `uppajjati` → both causatives reported as needing the verb added. Before the fix: both silently repointed.
- Reviewer's case 2, in memory with the corpus check disabled to reach the branch: `abhivādeti`, `uppādeti`, `uppādayati` go to the editor, not to a write.
- (a) and (r) on a present-verb grammar: "pr, caus of abhivadati" → pick gives "pr, caus of abhivadati", root gives "pr, caus of abhi √vad"; negation and trailing text preserved.
- Live dry run (scope: whole db): 0 to repoint, 1 needing a verb added, 0 undecided.
- `ruff check`, `ruff format`, `pyright` (scope: the three changed Python files) → pass.
- `just typecheck` (scope: whole repo) → 0 errors.
- Reviewer, earlier in this round: sampled all 53 `meaning_lit` causative hits and 15 of 112 root-sign hits, no false positives; all 422 group-8 exclusions correct; homonym numbers never written on any path; dry run read-only.

### Not verified
- No independent reviewer has seen the two fixes above; they were verified by the implementing agent only.
- CodeRabbit could not run.
- The corpus and paradigm paths of the missing-verb finder, and its gui2 loading, were not re-run.
- Data issue found, not this thread's: `nabhivadati` has grammar "pr" rather than "pr, from na abhivadati", so it is not recognised as a fused negative.

## Verdict
PASSED
- Date: 2026-09-25
- Reviewer: independent Sonnet agent; fixes and re-verification by the implementing agent.
