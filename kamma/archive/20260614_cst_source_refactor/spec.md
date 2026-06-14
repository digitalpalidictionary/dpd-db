# Spec: cst_source_sutta_example refactor

## GitHub issue
#157 "Refactoring" (`1-refactor, 2-repo, 3-python`) — ongoing tracker. This thread is **one step** of it and does **not** close the issue.

## Background / trigger
While fixing a sentence-splitting bug (variant-reading notes `[saṃ. ni. ...]` truncating examples — fixed in `tools/tokenizer.py` + `tests/tools/test_tokenizer.py`) it became clear that `tools/cst_source_sutta_example.py` is far too large and hard to navigate: **3145 lines in a single module**.

## Current shape (what's in the file)
- Module data: `CstSourceSuttaExample` namedtuple, `sn_peyyalas` (~120 rows), `sn_collapsed_vagga_counts`.
- `get_cst_filenames()`.
- `GlobalData` class — mutable state container + `make_cst_soup`, counter initialisers.
- Example extraction: `find_gatha_example`, `find_sentence_example`.
- ~12 small **pure** parsing helpers: `get_text_and_number*`, `clean_*`, `assert_*`, `is_int`, `split_sutta_number`.
- **~70 per-book handler functions** (`vin1_parajika` … `apt_abhidhanapadipikatika`) — the bulk, ~2450 lines. Each takes `GlobalData`, mutates `g.source`/`g.sutta`/counters.
- `find_cst_source_sutta_example()` — orchestrator with a ~170-line `match book:` dispatch to the right handler.

## Goal
Break the module into a coherent package with small, themed parts, **with zero behavioural change**. Readability/maintainability only.

## Hard constraints
- **Behaviour-preserving.** Output of `find_cst_source_sutta_example(book, text)` must be byte-for-byte identical before and after, for every book.
- **Public import API must not break.** Real callers import these names:
  - `find_cst_source_sutta_example` (gui2/pass2_pre_controller, gui2/dpd_fields_examples, exporter/analysis/passage_by_code, exporter/analysis/book_to_verses, archive/gui/*)
  - `CstSourceSuttaExample` (gui2/pass2_pre_view, pass2_pre_new_word_manager, pass2_pre_file_manager)
  - `make_cst_soup` (scripts/archive/*) — **NOTE:** currently only a `GlobalData` *method*, so these archive imports are already broken (`make_cst_soup` is not module-level). They call it as `make_cst_soup(pth, book, unwrap_notes=False)`, implying the intended public signature.
  These must keep importing from `tools.cst_source_sutta_example` unchanged.

## Second internal consumer — `passage_by_code.py` (found 2026-06-14)
`exporter/analysis/passage_by_code.py` also drives the engine manually via `GlobalData`
+ 4 bare prose handlers (`dn/mn/sn/an_*_nikaya`) + `clean_example`. **Decision: adapt it
to the new parser API** (C-adapt), guarded by a characterisation test on
`get_passage_by_code()`. Full write-up added after the refactor lands.
- Modern type hints, `pathlib.Path`, no `sys.path` hacks (per project rules).
- No logic "improvements" smuggled in — strict move-only. Any genuine bug found is noted, not silently fixed.

## Safety net (meticulous before/after testing — the heart of this thread)
Build a **characterisation (golden) test** BEFORE refactoring:
- For a representative set of book codes covering **every branch** of the `match` (at least one book per handler function), call `find_cst_source_sutta_example(book, ".")` (the "." pattern already used by `exporter/analysis` to match all sentences/verses) and snapshot the full returned list.
- Capture the baseline from current `main`, store as a fixture.
- After each refactor step, assert the output equals the baseline exactly.
- Keep the tokenizer fix already in place; the baseline is captured on the **post-tokenizer-fix** code so the fix is not mistaken for a regression.

## How we'll know it's done
- Package created; `tools/cst_source_sutta_example.py` either becomes a thin re-export shim or a package `__init__.py` re-exporting the public names.
- All existing importers run unchanged (import smoke test passes).
- Golden test passes identically before/after.
- ruff check, ruff format, pyright all clean on every new/changed file.
- `tests/` suite green.

## What's NOT included
- No behaviour changes, no new features, no bug "fixes" beyond the already-landed tokenizer fix.
- Not closing issue #157.
- No change to the per-book parsing logic itself (only its physical location).
