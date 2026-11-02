# Spec: small memory savings for contributor gui2 instances

**Thread:** 20261102_contrib_mem_savings
**Date:** 2026-11-02
**GitHub issue:** [#215 — Contributor Onboarding](https://github.com/digitalpalidictionary/dpd-db/issues/215). Never write to the issue.
**Builds on:** `kamma/threads/20261102_contrib_mem_measure/` (read its `artifacts/results.md` first; its probe and numbers are the baseline here).
**Plan:** `plan.md` in this folder.

## Overview

One contributor gui2 instance holds 1,165.9 MB when warm and 1,485.0 MB after one
Pass1Auto book (server, 2026-11-02; `contrib_mem_measure/artifacts/server/results.md`).
Alice's live instance held 1,542.8 MB after about 23 hours. Expected load: up to 3
contributors now, 4 to 8 later. The owner will do the big rebuild (one process for all
users) only when there are more than 8 contributors.

This thread finds the **small, safe changes** that cut the per-instance memory now, and
ships the ones that pay off. It measures first, on the laptop, and puts a gate before any
code change. The server is used once, at the end, to confirm the real instance.

Target, not a promise: move one instance from about 1.49 GB toward 1.0 GB, so that 8
contributors fit on a 16 GB server with room to spare.

## What was verified (read from the source on 2026-11-02)

- A contributor sees only **Pass1Auto and Pass1Add** by default (`gui2/contributor_tabs.py:9-11`; extra tabs only through `DPD_GUI2_TABS`). The role is `contributor-server` (`gui2/user.py:54-58`, `is_server_contributor`).
- `DatabaseManager.load_corpus()` loads every headword as a full ORM object. It defers only five columns: `inflections_html`, `freq_html`, `inflections_sinhala`, `inflections_devanagari`, `inflections_thai` (`gui2/database_manager.py:181-204`).
- Bytes of text per column in the laptop `dpd.db` (89,774 rows, 59 columns, read-only query on 2026-11-02): `freq_html` 694.9 MB, `inflections_html` 265.0 MB, `freq_data` 61.9 MB, `inflections_sinhala` 47.4 MB, `inflections_thai` 39.0 MB, `inflections_devanagari` 24.7 MB, `inflections` 24.7 MB, `example_1` 8.1 MB. Total 1,195.4 MB. The text actually loaded (total minus the five deferred columns) is about **124 MB**, yet the corpus step costs **676.4 MB**. The rest is Python overhead: 59 attributes on each of 89,774 objects.
- Only two things read the corpus for a contributor: `make_inflections_lists` (`gui2/database_manager.py:346-364`) and the synonym detector (`tools/synonym_variant.py:885-905`, built by `get_relationship_detector`, `gui2/database_manager.py:781-799`). Pass2 and the Tests tab also call `load_corpus` but a contributor never sees them (`gui2/tests_tab_controller.py:287,853`; `database_manager.py:408,435`).
- The detector keeps the whole list of headword objects (`self._headwords = list(headwords)`, `tools/synonym_variant.py:889`). It reads these attributes: `lemma_1`, `meaning_1`, `pos`, `grammar`, `construction`, `root_key`, `root_sign`, `root_base`, `family_root`, `var_phonetic`, `var_text`, `synonym`, `variant`, `id`, and `freq_data` (only in `has_textual_occurrence`, `tools/synonym_variant.py:351-358`). This list comes from a scan of the file and is not proven complete. The plan finds the exact set with `raiseload`.
- `all_inflections` has **one reader**: the membership test `word not in self.db.all_inflections` (`gui2/pass1_auto_controller.py:273`).
- `all_inflections_missing_meaning` has **no reader** outside its own builder (`gui2/database_manager.py:75,356-363`) and one test (`tests/gui2/test_database_manager_corpus.py:202-203`).
- `make_inflections_lists` calls the cached property `inflections_list_all` on all 89,774 objects (`gui2/database_manager.py:358-360`). A cached property stores its list on the object for the life of the process. This may be a large part of the 234.8 MB that step costs. Not yet measured.
- Pass1Add has a "refresh DB" button that marks the corpus stale (`gui2/pass1_add_view.py:243-246`). The next load builds a second full corpus while the detector still holds the first rows (`tools/synonym_variant.py:889`). The extra memory is not measured yet; the plan has a variant for it. A contributor's save does not trigger this: it writes JSON (`gui2/save_router.py:38-52`).
- The app warm-up builds the word finder, the AI manager, the bold-search manager and the detector (`gui2/main.py:558-583`). It never builds the inflection lists; Pass1 builds them on first use (`gui2/pass1_auto_controller.py:120,198`; Pass1Add at `gui2/pass1_add_view.py:229`).
- The Pass1Add controller builds the word finder at once (`gui2/pass1_add_controller.py:51`), and Pass1Auto builds the AI manager at once (`gui2/pass1_auto_controller.py:32`). A contributor who opens both tabs pays for both whatever the warm-up does.
- The word finder loads `cst_file_freq.json` (70.9 MB on disk) into one dict per file, `file -> {word: count}` (`tools/wordfinder_manager.py:35,51-53,102-107`). JSON loading makes a separate string for each word in each file, so the same word is stored many times. Not yet measured.
- Measured costs (laptop, isolated, MB): corpus 676.4, inflection lists 234.8, word finder 172.1, `initialize_db` 121.2, imports 49.7, AI manager 34.4, spell checker 17.1, detector 15.6 (staircase 66.7), bold search 1.0 (`contrib_mem_measure/artifacts/laptop_tables.md`).

## What it should do

The work has three stages and one gate.

### Stage 1 — Measure each lever on the laptop (no code change in `gui2/` or `tools/`)

Each candidate lever is built in a throwaway script in `artifacts/`, in a fresh process,
three runs per variant, against a `.backup` copy of `dpd.db`. The same safety rules as the
earlier thread apply: contributor role set, `PRAGMA query_only`, 1.5 GB system cap plus an
in-process watchdog, no write outside this folder and a temp dir.

| Lever | What it changes | Variants to measure | Why it might pay |
|---|---|---|---|
| L1 slim corpus | A contributor loads only the columns its two consumers read, with `load_only` | full (today), needed columns, needed columns without `freq_data` | 59 attributes on 89,774 objects is most of the 676 MB |
| L2 direct inflection sets | Build `all_inflections` from a plain column query, not from objects and cached properties | today (corpus then sets), direct query | the cached lists stay on every object |
| L3 drop the dead set | Do not build `all_inflections_missing_meaning` | with, without | no reader outside the builder |
| L4 word finder strings | Share one string per word across the per-file dicts (`sys.intern`), same search results | today, interned | the same word is stored many times |
| L5 lookup instead of set (earlier "C") | Ask the `lookup` table whether a word is a headword inflection, no in-memory set | set (today), no set | removes the whole inflection set; needs equivalence and latency numbers |
| L6 lazy managers (earlier "B") | Build the word finder, AI manager, bold search and detector on first use | measure only what a contributor who opens both tabs still pays | likely small; the tabs build them anyway |

Also measured: the sum of the chosen levers in one process (the contributor staircase),
and the start-up peak (VmHWM) of each variant.

Equivalence numbers gathered in the same stage, because a saving that changes behaviour is
not a saving:

- **L1:** the detector returns identical synonym and phonetic-variant lists for a fixed sample of headwords on a full and on a slim corpus. A `raiseload("*")` run finds every column the consumers touch, so nothing is lazy-loaded by accident.
- **L2/L5:** `all_inflections` from the direct query equals today's set exactly. For L5, the count of differences between the set and the `lookup` keys with a non-empty `headwords` column, and the time per query over a real word list.
- **L4:** word finder results are identical for a fixed list of queries and all three search types.

### Gate (owner decides)

The thread stops after Stage 1 and presents a table: lever, MB saved per instance
(median, min–max), equivalence result, effort, risk. The owner picks which levers to
build. Default proposal: build a lever only if it saves at least **100 MB per instance**
and its equivalence check is clean. The owner may change the threshold or pick any lever.
`all_inflections_missing_meaning` is only removed if the owner says so (it has a test).

### Stage 2 — Build the chosen levers, contributors only

- A lever changes behaviour **only when the role is `contributor-server`**. The desktop app keeps today's code path. This is the default; the owner can widen it at the gate.
- Each lever gets a test written first, and a revert check (revert the change, run the test, count the failures).
- No new dependency. No change to the database file.

### Stage 3 — Confirm on the server

The owner commits and pushes. The server pulls. An agent messages the server agent through
`herdr-remote` (see `~/.agents/skills/herdr-remote/SKILL.md`). Same phases as the earlier
thread: restart alice, then readings at +15 s, after "Database loaded.", after "All tabs
and tools ready.", and after one `mn` book. The owner opens the page in the browser and
says yes before each restart. The result is a before and after table against 1,165.9 MB
(warm) and 1,485.0 MB (one book), and an updated projection for 3, 8 and 16 contributors.

## Assumptions & uncertainties

Assumed:
- A contributor uses Pass1Auto and Pass1Add and nothing else. Extra tabs through `DPD_GUI2_TABS` are not covered; a slim corpus must not break them, and the plan checks which of them read the corpus.
- The laptop `dpd.db` is close enough to the server's for relative savings. The two databases have the same 89,774 headwords and 88,805 rows with frequency data, and the earlier thread's staircase gave 1,385.6 MB on the laptop and 1,391.7 MB on the server.
- A per-instance saving measured by the probe holds in the real app, within a few MB. The earlier thread showed the probe and the app agree to 4.7 MB once the inflection lists are left out.

Not verified:
- How much each lever really saves. That is Stage 1.
- Whether the detector or any contributor path reads a column that a slim corpus leaves out. `raiseload` answers this in Stage 1.
- Whether `sys.intern` changes the word finder's memory enough to matter, and whether it changes search order. Stage 1 answers both.
- Whether the `lookup` table lists every headword inflection that `all_inflections` holds (L5).
- The cost in seconds of per-word queries for L5 in a long Pass1Auto text.
- Whether the earlier probe's isolated detector figure (15.6 MB) or its staircase figure (66.7 MB) is right.

## Constraints

- No change to `gui2/` or `tools/` before the gate. Stage 1 writes only in this thread's `artifacts/`.
- Never read, print or edit `config.ini` or any `.env`. Never touch the live `dpd.db`: work on a `.backup` copy. Never write to `shared_data/` or the spell-checker dictionaries.
- Memory probes follow the standing rules: tell the owner first, cap at 1.5 GB, check for stray processes afterwards. The owner says yes once for the whole capped batch.
- No git command and no commit by the agent. The owner commits.
- Server work only through the server agent, only after the owner has pushed and said yes to each restart. Never touch `~/epitaka-translator` on the server.
- Lint, format and type-check every touched file (`ruff`, `pyright`; for `gui2/` use `--project /dev/null`), run `just typecheck`, and run the related tests.
- Never write a derived value back onto a tracked ORM attribute (project rule for SQLAlchemy objects).

## How we'll know it's done

1. `artifacts/lever_results.md` has, for every lever, median, min and max of the saving in MB, the equivalence result, and the start-up peak. Every number comes from a probe output line in `artifacts/`.
2. The owner has picked the levers at the gate, and the pick is recorded in this folder.
3. Each chosen lever has a test that fails when the lever is reverted, and all related tests, lint, `pyright` and `just typecheck` pass.
4. The server readings after the change are in `artifacts/server/`, with a before and after table.
5. The desktop path is unchanged: the full corpus test and the existing corpus tests still pass for the non-contributor role.

## What's not included

- Option E (one process for all users). The owner does that after more than 8 contributors.
- Moving the frequency data into the database (earlier "D") beyond the interning test in L4.
- Any change to the AI manager's providers, or to the Flet UI.
- A direct measure of Flet's per-session UI cost.
- Editing the earlier threads. Corrections stay listed in `contrib_mem_measure/artifacts/results.md`.
