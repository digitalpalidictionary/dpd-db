# Spec: cst_source latent bugs (carried over from the refactor)

## Origin
During the `cst_source` refactor (now landed, archived at
`kamma/archive/20260614_cst_source_refactor/`) the work was **strict move-only**:
any latent bug spotted while porting was *noted, not fixed*, because fixing it
would have broken old-vs-new parity. Those notes lived in that thread's
`findings.md`. This thread exists to actually deal with the **unsolved** ones.

Related issue: **#157** "Refactoring" (ongoing tracker) — does NOT close it.

## ⚠️ These are OUTPUT-CHANGING, not cosmetic
Unlike the refactor, fixing #6 and #7 changes the **real extracted data**
(`source` codes / `sutta` text) that flows into the dictionary build (lookup
tables, exports). So each fix needs:
1. domain confirmation that the "fixed" value is actually correct, and
2. a check of downstream consumers of the changed `source`/`sutta` string.
Do NOT treat these as a quick lint pass.

## The findings to resolve

### A. `ap`/`apt` prefixes are cross-wired and `APP` is bogus  (`tools/cst_source/parsers/misc.py`)
> CORRECTION (2026-06-14): the original framing below was WRONG. It assumed
> `ap` legitimately uses `APP` and only `apt` was buggy. In fact `abbreviations.tsv`
> registers exactly two codes — `AP` = Abhidhānappadīpikāpāṭha (root text, book `ap`)
> and `APt` = Abhidhānappadīpikā Ṭīkā (commentary, book `apt`). `APP` is NOT a real
> book code. Both parsers were wrong and cross-wired:
> - `ApParser` (`ap`) emitted `APP` → must be `AP`.
> - `AptParser` (`apt`) emitted `AP` (which is actually ap's correct code) → must be `APt`.
>
> RESOLUTION: fixed both parsers (`misc.py`: `ApParser` `APP`→`AP`, `AptParser` drop
> the dead `book = "AP"` overwrite so it keeps `APt`). Migrated the 5 shipped
> `source_1` values in `dpd.db`: `APP1`→`AP1`, `APP2.4`→`AP2.4` (ap);
> `AP2.5`→`APt2.5`, `AP3.3`→`APt3.3`, `AP2.3`→`APt2.3` (apt). `generate_books_tsv.py`
> already registered `AP`+`APt` (never `APP`), so no downstream collision; the
> apadāna codes (`APA…`/`API…`) are distinct strings.

~~`AptParser.update` sets `book = "APt"` then immediately overwrites it with~~
~~`book = "AP"` … No ID collision (`ap` uses prefix `"APP"`)~~ — superseded by the
correction above.

### B. `abh2` leaks literal "xxxxxxx" placeholder  (`tools/cst_source/parsers/abhidhamma.py:112`)
`Abh2Parser.update`: when `not self.vagga`, it does
`self.sutta = f"xxxxxxx, {sutta}".lower()`. A debug placeholder reaches real
output for vagga-less `abh2` (vibhaṅga) subheads.
- **Decide:** what should the prefix be when there is no vagga? (Likely the
  section name, mirroring the non-abhidhamma fallbacks, or just `{sutta}` alone.)
- **Check:** grep current built data / exports for `xxxxxxx` to gauge blast radius.

### C. `kn17` dead branch → `UnboundLocalError`  (`tools/cst_source/parsers/khuddaka.py:485`)
`Kn17Parser.update` final branch:
`self.sutta = f"{vagga}, {section}".lower()` references function locals
`vagga`/`section` that are only bound in other branches — would raise
`UnboundLocalError` if it ever ran. It never fires on real data (parity was
byte-identical), so it is dead code.
- **Decide:** fix to `self.vagga`/`self.section` (the obvious intent), OR delete
  the unreachable branch entirely. Either way, add a test that constructs the
  triggering subhead to prove current reachability before changing it.
- **RESOLVED (2026-06-14): DELETED.** Real-life probe over `s0517m.mul.xml` (124
  subheads): full parse raised nothing and the branch condition was met 0 times.
  Genuinely dead copy-paste residue from a prior book. A `@pytest.mark.slow` test
  now guards that the condition stays at 0 and a full kn17 parse never raises.

### D. `x["n"]` (str) assigned to int-typed `sutta_counter`  (benign type smell)
`sutta.py:178` (Anguttara), `commentary.py:417`, `commentary.py:448` (ANa/ANt):
`self.sutta_counter = x["n"]` stores a `str` into a counter that elsewhere holds
`int`. No runtime bug today (only f-string interpolation on that path), but it is
a real typing inconsistency. Lowest priority; fold into a typing cleanup.

## How we'll know it's done
- Each of A/B/C resolved with a deliberate decision recorded (fix vs. leave-with-reason).
- New unit tests for any behaviour change (esp. A and B: assert the corrected
  `source`/`sutta` for a representative chunk; C: a reachability test).
- Downstream impact of any changed `source`/`sutta` string assessed.
- `tools/cst_source` is ruff/pyright-excluded — verify changes by test, not lint.
- Full `uv run pytest tests/` green (incl. `-m slow` for the cst_source parity/regression).

## What's NOT in scope
- Resolved/non-issues from the old findings.md (#1 make_cst_soup param, #2/#3/#5)
  — already handled or n/a.
- Re-architecting the parsers. These are targeted data-correctness fixes.
