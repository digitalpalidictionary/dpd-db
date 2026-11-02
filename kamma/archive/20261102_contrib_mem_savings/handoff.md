# Handoff (2026-11-02) — contrib_mem_savings

Resume with `/kamma:2-do 20261102_contrib_mem_savings`. Read `spec.md`, `plan.md` (the DRIFT note above task 3.1), `artifacts/decision.md`, `artifacts/lever_results.md`, `artifacts/equivalence.md`.

## State
- **Phases 0 to 2 done.** Laptop measurements: 96 rows in `artifacts/laptop.jsonl`, all ok, guard clean. Equivalence checks (a) to (e) PASS. Gate applied by the default rule (owner said "keep going"): see `decision.md`.
- **Result:** split contributor corpus + compact inflection sets take the contributor build from 1,386.3 MB to 904.6 MB (−481.7 MB), start-up peak 1,432 → 967 MB. Estimated per instance after one book on the server: about 1,003 MB (today 1,485.0 MB).
- **Code written (uncommitted):** `gui2/database_manager.py` (contributor branches in `load_corpus`, `make_inflections_lists`, `mark_corpus_stale`; new `_load_contributor_corpus`, `_make_contributor_inflections_lists`, `CONTRIBUTOR_CORPUS_COLUMNS`), `tools/hashed_words.py` (new), `tests/tools/test_hashed_words.py` (new), `tests/gui2/test_database_manager_corpus.py` (8 new tests, 2 existing ones narrowed with `isinstance` because the sets are typed `Container[str]`).
- **Checks done:** `ruff check`, `ruff format`, `pyright` clean on those four files; 31 tests pass; revert check done (3 failures with the contributor branches off, 5 with the hash lookup broken); files restored and re-verified.

## To do next (plan tasks)
1. **3.7:** run `uv run pytest tests/gui2 tests/tools -q` (note any test already broken before), and `just typecheck` (pyrefly). Re-check the diff size of `gui2/database_manager.py` (it was clean: only the intended lines).
2. **3.8:** add variant `contributor_real` to `artifacts/lever_probe.py` (real `DatabaseManager` in contributor role, real managers) and run it 3 times under the cap; its total must be within 5 % of `contributor_split_hash` (904.6 MB). Same caps as before; the owner said to keep going without asking for a yes on capped runs.
3. **Phase 4:** the owner commits and pushes. Then message the server agent through the `herdr-remote` skill (host `epitaka`, pane `w1:p1`; confirm with `pane read`): `git pull` once, then the phase readings (plus15s, db_loaded, warmup_done, one_book, pass1add) as in plan 4.3. The owner opens the page and says yes before each restart of `dpd-gui@alice`.
4. **Phase 5:** `artifacts/results.md` (before and after on the server, projection for 3, 8 and 16 contributors), done check, then `/kamma:3-review` and `/kamma:4-finalize`.

## Facts a fresh session needs
- Scratchpad (this session's): `/tmp/claude-1000/-home-bodhirasa-MyFiles-3-Active-dpd-db/212a07c4-9a04-409b-9eee-e92c985ca66f/scratchpad/`. The database copy is `dpd_copy.db` there (2.3 GB, 89,774 headwords, same as the live file). If that folder is gone, make a new copy with `sqlite3 dpd.db ".backup <new path>"`.
- Run probes from the repo root: `PYTHONPATH=. uv run kamma/threads/20261102_contrib_mem_savings/artifacts/lever_probe.py ...`. Each child runs under `systemd-run --user --scope -p MemoryMax=1500M -p MemorySwapMax=0`, one core, no network, read-only on the copy.
- Known risk, not fixed: after "refresh DB" on a slim corpus the extra memory is 284.9 MB (full corpus: 172.5 MB) because the detector keeps the old rows.
- Hypotheses that failed (do not retry): interned word finder (costs 26.6 MB), direct sets (72 MB, replaced by the compact set), `lookup` table instead of the set (not equivalent), lazy managers (contributors use them).
- No git command and no commit by the agent; the owner commits. Tests for `gui2/` and `tests/` need `uv run pyright --project /dev/null <file>`.
- The `herdr-remote` skill is in `~/.agents/skills/herdr-remote/SKILL.md`.
