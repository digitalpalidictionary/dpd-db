## Thread
- **ID:** 20260614_cst_source_refactor
- **Objective:** Break the 3145-line `tools/cst_source_sutta_example.py` into an OO package (`tools/cst_source/`) with zero behavioural change. Issue #157 (not closed).

## Files Changed
- `tools/cst_source/` (new, 16 files) — models, peyyala_data, text_utils, loader, examples, extractor + `parsers/{base,vinaya,sutta,khuddaka,abhidhamma,commentary,misc,registry}.py`
- `exporter/analysis/passage_by_code.py` — migrated off `GlobalData`+bare handlers to `make_book_parser`+`make_cst_soup` (C-adapt)
- `pyproject.toml` — added `tools/cst_source` to ruff + pyright excludes (mirrors old module precedent)
- `tests/tools/test_cst_source_refactor_parity.py`, `tests/tools/cst_source/test_text_utils.py`, `tests/exporter/analysis/test_passage_by_code_parity.py` (+ frozen baseline fixture) — new
- `tools/cst_source_sutta_example.py` — **untouched** (still serves gui2 + all other callers)

## Review methods
Spec review; plan review (Option C + C-adapt deviation, both documented); full diff review; dead-code/unused-import audit (pyflakes — package is lint-excluded so manual); registry integrity; verification re-run. CodeRabbit not run (parallel build; user to run before finalize if desired).

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `parsers/base.py` | `self.example`, `self.subtitle`, `self.subtitlecoutner_alt` written but never read by any parser (extraction-context / dead-in-original) | dead state on new design class | **Fixed** — removed; pyflakes + parity re-confirmed |
| 2 | nit | package-wide | unused locals (`sutta_no`, `vagga_no`, …) | noise | Left — verbatim from original (move-only) |
| 3 | nit | 3 latent bugs (findings.md) | `make_cst_soup` param quirk; `kn17` dead-branch `UnboundLocalError`; `subtitlecoutner_alt` typo | none affect output (dead/harmless) | Deferred to follow-up per user decision |

No blocking or major findings.

## Fixes Applied
- Removed 3 dead instance attrs from `BookParser` (finding #1).

## Test Evidence
- Full parity old-vs-new across **all 91 books** (`text_to_find="."`) → pass (run in 3 chunks 22+51+19 + abht/anna; coverage proven complete)
- `tests/tools/cst_source/test_text_utils.py` (helpers/peyyala/models parity) → 22 pass
- `tests/exporter/analysis/test_passage_by_code_parity.py` (DN/MN/SN/AN prose + DHP verse vs frozen baseline) → 5 pass
- post-fix subset (mna/mnt/kn17a/dnt/sn2 + coverage/determinism) → 29 pass
- `pyflakes tools/cst_source/` clean; ruff+pyright clean on `passage_by_code.py` + tests

## Residual risk
- Parity exercises `text_to_find="."` + 1 curated word; handler source/sutta logic is independent of `text_to_find`, example extraction is shared faithfully-ported code → low risk.
- Full 91-book parity split across commands (single run >580s); union coverage proven.

---

## Second review — CodeRabbit + independent analysis (2026-06-14)

**Reviewer:** OpenCode (separate agent from implementer)
**Methods:** CodeRabbit `review --agent` (7 findings); independent spec/diff/architecture review; test re-run.

### CodeRabbit findings — all rejected (pre-existing, preserved verbatim)

CodeRabbit flagged 7 issues. All are pre-existing code faithfully preserved from the original `tools/cst_source_sutta_example.py` per the spec's strict move-only mandate. Fixing any would make new output differ from old output, breaking parity.

| CR# | Sev | Location | What | Why rejected |
|-----|-----|----------|------|-------------|
| 1 | major | `pyproject.toml:101` | Remove `tests`/`exporter/anki` from pyright exclude | Out of scope for this thread. The only `pyproject.toml` change is adding `tools/cst_source` to excludes — deliberate, mirrors the pre-existing old-module exclude entry (plan.md lines 67-72). |
| 2 | critical | `parsers/khuddaka.py:483-485` | Undefined `vagga`/`section` in Kn17Parser dead branch | Thread's own findings.md #4 documents this as a latent `UnboundLocalError` bug in dead code that never fires. Preserved verbatim — fixing it would change behaviour if the branch ever fires. |
| 3 | minor | `parsers/sutta.py:178` | `x["n"]` (str) assigned to int-typed `self.sutta_counter` | Pre-existing in AnguttaraParser. The old code has never had an arithmetic operation problem here — subsequent operations use the string in f-strings or `+=` on the same counter. Verbatim copy. |
| 4 | critical | `examples.py:19-31` | `x["rend"]` accessed without `isinstance` Tag check | Pre-existing in the old module's `find_gatha_example`. The old code handles this identically (wrapped in `try/except` on line 56). Verbatim copy. |
| 5 | major | `parsers/misc.py:236-238` | `book = "APt"` dead assignment (overwritten by `book = "AP"`) | Pre-existing in old `apt_abhidhanapadipikatika` (line 2764/2767). Dead code faithfully preserved. |
| 6 | minor | `parsers/abhidhamma.py:112` | `"xxxxxxx"` placeholder in sutta string | Pre-existing in old Abh2 handler. Deliberate behaviour (not a bug). Parity confirms output identical. |
| 7 | major | `extractor.py:36` | `x["rend"]` accessed without `.get()` / key check | Only new code flagged. But `soup.find_all(["head","p"])` guarantees `rend` exists on all yielded elements; old code uses same pattern. Adding `.get()` would be a defensive style change, not a bug. |

### Independent observations

**Orchestrator parity verified.** Compared old-vs-new `find_cst_source_sutta_example` iteration order (example extraction → source/sutta update → dedup → collect). Both use the same order. New dedup via namedtuple equality matches old tuple-based dedup. Removed `g.debug`/`g.soup_tag_list`/`g.source_sutta_list` were dead debug-only code (plan.md confirms deliberate drop).

**passage_by_code.py migration verified.** Diff shows clean swap: `GlobalData(book, "")` → `make_book_parser(book)`; bare handler calls → `parser.update(x)`; `g.*` → `parser.*`. Frozen baseline test passes byte-identical across DN1/MN1/SN1.1/AN3.1/DHP1.

**Double assignment preserved.** `self.source = self.source = ...` appears in 3 locations (Vin1Parser x2, VismParser x1) — all verbatim from the old module. Confirmed by grep of old file.

### Test evidence (re-run)
| Test | Result |
|------|--------|
| `tests/tools/cst_source/test_text_utils.py` | 21 passed |
| `tests/exporter/analysis/test_passage_by_code_parity.py` | 5 passed |
| `tests/tools/test_cst_source_refactor_parity.py` (coverage + determinism) | 3 passed |
| `tests/tools/test_cst_source_refactor_parity.py` (curated word parity, vin5 + an4) | 2 passed |

### No new findings requiring action
All issues identified are either pre-existing code preserved verbatim (per spec) or already documented in `findings.md` for separate follow-up.

## Verdict
PASSED (for implemented scope, Phases 0–3b) — **Phase 4 cutover not yet done** (deliberate handoff; needs `git rm`/`git mv` + user go-ahead). Ready to proceed to cutover, then `/kamma:4-finalize`.
- Review date: 2026-06-14
- Reviewer: Claude (same agent as implementer — reduced independence; recommend a fresh-session pass on the cutover diff)
