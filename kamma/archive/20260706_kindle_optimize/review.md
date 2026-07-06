# Review: Optimize the kindle exporter

Method: `/code-review high` — 8 parallel fresh-context finder agents (line-by-line,
removed-behavior, cross-file tracer, reuse, simplification, efficiency, altitude,
CLAUDE.md conventions), findings deduped and independently verified.

## Findings acted on

1. **Design: `_HtmlFriendlyHeadword` proxy over-engineered** (4/8 angles:
   reuse, simplification, altitude, efficiency, independently convergent).
   The `__getattr__`-based proxy diverged from the established sibling
   pattern (`DeconstructorData`/`GrammarData`: flat plain data, no ORM
   proxy), required a `cast(DpdHeadword, self.i)` hack to satisfy
   `make_grammar_line`'s type hint, added a Python-level function call +
   dict lookup on every attribute access, and eagerly computed all 12
   escaped fields even for the ~29.5% of headwords with no `meaning_1`.
   **Fixed:** redesigned to `_make_friendly(i) -> dict[str, str]`, computed
   only when `meaning_1` is truthy; `KindleData.i` is now the real,
   never-wrapped `DpdHeadword`; two jinja templates updated to read the
   escaped fields from a `friendly` dict. Re-verified byte-identical at
   full scale after the redesign.

2. **Bug: `html_friendly(None)` crash risk** (3/8 angles: line-by-line,
   removed-behavior, cross-file, independently convergent). Deduplicating
   `html_friendly` dropped the old try/except; `save_abbreviations_xhtml_page`
   calls it unguarded on values from `csv.DictReader` (`restval=None` for a
   short/ragged TSV row). Currently dormant (0 ragged rows in
   `abbreviations.tsv` today) but a real latent regression from "silently
   pass through" to "crash the whole export." **Fixed:** explicit
   `isinstance(value, str)` skip at the call site, matching the guard style
   already used in `_make_friendly` — not a blind try/except.

3. **Inaccurate comment on the `getmembers` monkeypatch** (3/8 angles:
   line-by-line, altitude, cross-file). The comment claimed the reflection
   scan was "never" used with real pre/post options elsewhere in the
   codebase — false (`tools/translit.py`, `tools/sinhala_tools.py`,
   `audio/bhashini_class.py` do). **Fixed:** rewrote the comment to state
   the actual justification (the scanned modules never register functions
   dynamically, so the cache is safe for every caller, not just
   `lemma_ipa`).

4. **Missing/old-style type hints** (conventions angle): `KindleData.__init__`
   missing `-> None`, `make_words_in_deconstructions`/`make_deconstructor_words_set`
   using bare `set` instead of `set[str]`, test helper `_env()` missing a
   return type. **Fixed**, all four.

## Findings considered, not acted on

- **`lru_cache` test-pollution risk** on `_lemma_ipa_transliterate` (a
  process-wide cache keyed by text could serve a stale value if some test
  mocked `transliterate.process` differently for the same text). Checked:
  no current test does this — the one aksharamukha stub
  (`tests/exporter/mobile/test_mobile_exporter.py`) uses
  `sys.modules.setdefault`, a no-op once the real package is already
  imported by `db.models`, which happens in every real collection order.
  `tests/db/test_models_lemma_ipa.py` already calls `cache_clear()`
  defensively. Judged unreachable today; no fixture machinery added for a
  problem that doesn't exist.
- **`html_friendly` duplicates `exporter/goldendict`'s `_NewlineView`**
  (reuse angle). Real, but the two have different escaping requirements
  (kindle: `<br/>` + angle-bracket escaping for strict XHTML; goldendict:
  bare `<br>`, no escaping) and unifying them is a cross-exporter
  consolidation — a separate, bigger follow-up, out of this thread's scope.
- **`tools/deconstructed_words.py` duplicates `Lookup.deconstructor_unpack`'s
  JSON-parse logic** (reuse/simplification). True, but it's one line,
  exists specifically to avoid the ORM-row-construction cost the fix
  targets, and a shared helper for one line adds more indirection than it
  removes.
- **Stale caller in `archive/exporter/kindle/kindle_exporter.py`**: dead
  code, excluded from lint/tests/imports, no live risk.

## Post-review verification

- Full-scale parity vs the original pre-review baseline: `ALL-IDENTICAL
  (80 files, 2 excluded)`.
- Clean-process timing after the redesign: 36.92s vs the 58.25s baseline
  (~1.58×) — consistent with (and slightly better than) the pre-review
  measurement; the redesign was not a regression.
- `uv run ruff check --fix` / `ruff format` / `pyright` clean on every
  touched file.
- `uv run pytest tests/` → 1204 passed, 9 failed (pre-existing, unrelated,
  reproduced on a clean `git stash` — see plan.md Results), 16 deselected.

## Verdict

Pass. All CONFIRMED/PLAUSIBLE findings with a real fix were applied and
re-verified; findings correctly scoped out are documented with reasoning.
Ready for finalize.
