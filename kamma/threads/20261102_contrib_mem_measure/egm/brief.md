# EGM brief — contrib_mem_measure (2026-11-02)

## Request
Measure accurately where the memory of one contributor gui2 web instance goes
(about 1.25 GB per instance). Goal: a measured split by component so the
memory-reduction options can be ranked on numbers. Measurement only: no gui2
code changes in this thread. Part of issue #215 (contributor onboarding).

Options to rank afterwards:
A measure first; B no warm-up preload for contributors; C answer "is this word
known" from the lookup table instead of an in-memory inflections set; D frequency
data in the db; E one process for all users with shared read-only data;
F start an instance only while its user is online.

## Anchored hypothesis
One contributor instance uses about 1.25 GB, but nobody knows how that splits,
so the options cannot be ranked. This thread builds a read-only probe that
loads each component in its own fresh process and reads its memory, reads the
live server instance from /proc (through the server agent), and measures how
memory grows as books are opened. Output: a table of numbers and a ranking of
options A-F. No gui2 change.

## Facts verified in the source (claims to re-check, not facts)
- Only measured number: one warm instance, RSS 1.25 GB, VmHWM 1.25 GB, after book
  runs and additions (kamma/archive/20261101_contrib_6_e2e_server_test/artifacts/server/results.md, "Addendum B"). Box: 2 vCPU, 7940 MB.
- gui2/main.py:`main(page)` builds `App(page)` per session; `App` builds `ToolKit(page)` (gui2/main.py:126) which builds a `DatabaseManager` per session (gui2/toolkit.py).
- gui2/main.py:~665 `claim_session`: "One live app per process"; the comment says a second tab "would build a second copy of the app (~2.5 GB)". A new page retires the old one but the old App stays in memory.
- `DatabaseManager.load_corpus()` (gui2/database_manager.py:181) loads all 89,763 `DpdHeadword` rows as ORM objects, defers five big HTML columns.
- `make_inflections_lists` builds `all_inflections` from `inflections_list_all` of every headword; Pass1Auto `is_missing` (gui2/pass1_auto_controller.py:271) tests membership in it.
- After the db loads, `_warmup_in_background` (gui2/main.py:558) builds every visible tab, then touches wordfinder_manager, wordfinder_popup, ai_manager, bold_definitions_search_manager and the relationship detector.
- `WordFinderManager.__init__` does `json.load` of cst_file_freq.json (70.9 MB on disk). shared_data/frequency/*.json total about 200 MB on disk.
- `AIManager.__init__` imports and builds several provider managers (claude, codex, openai-compatible ones if a key is set, gemini if a key is set).
- gui2/books.py: `SuttaCentralSource.segment_dict` and `word_dict` are `cached_property` on module-level `sutta_central_books`; each book a contributor opens builds and keeps its text index for the life of the process. sc_bilara_data is 261 MB on disk; CST romn_txt is 110 MB.
- `tools/spelling.py` `CustomSpellChecker` is a process singleton; the first caller's user_dict wins.
- Contributor role (`DPD_GUI2_ROLE=contributor-server`) makes db sessions `PRAGMA query_only = ON` (db/db_helpers.py:~75).
- `psutil>=7.0.0` is already a dependency. Python 3.13.
- A startup probe pattern exists: kamma/archive/20260918_gui2_startup_latency/artifacts/probe_warmup.py.
- Importing tools modules does not call load_dotenv (rg finds none). `tools/ai_manager.py` reads keys through `tools.configger.config_read` (config.ini). `tools/ai_manager.py` starts a probe thread only if the `agy` executable is on PATH.

## Rules that apply
- User runs scripts. Memory probes: `ulimit -v 1500000`, run once, tell the user first (feedback_memory_probe_caps).
- Never read or print config.ini or .env. Importing code that calls config_read reads config.ini; a probe must not print key values or make network calls.
- dpd.db is 2.2 GB; a probe must never write to it.
- Server work goes through the server agent (read-only commands only).
