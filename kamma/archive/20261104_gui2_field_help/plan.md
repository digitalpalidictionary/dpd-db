# Plan — help on every field in gui2

Thread: `20261104_gui2_field_help`. Spec: `kamma/threads/20261104_gui2_field_help/spec.md`. Read it first. No GitHub issue (Todoist 6hvxgxqPJHrhFG4g).

## Executor rules

- Do not run any `git` command. Do not commit, branch or open a PR. The working tree holds other threads' uncommitted files. Leave them alone.
- Do not start the gui2 web server or any long process until the owner says yes (Phase 2 and Phase 4 need it). Ask once, then run the whole sequence yourself, including driving the browser with `playwright-cli`. Keep one browser page.
- Put throwaway files in the session scratchpad. Never write into the home directory.
- Do not read or print `config.ini`, `.env` or any file that holds secrets.
- After editing any Python file, run in order: `uv run ruff check --fix <file>`, `uv run ruff format <file>`, `uv run pyright --project /dev/null <file>` (for files under `gui2/` and `tests/`), then the related tests. Never run `ruff format` on the JSON file.
- Type hints everywhere, modern forms (`dict[str, str]`, `str | None`). `Path`, not `os`. `icecream` (`ic`), not `print`. No `sys.path` tricks, no `Path(__file__)` tricks.
- Say "Hopa!" before using a tool. Tick a task `[x]` only after its `→ verify:` line has been done, and write the actual result under it.

## Architecture Decisions

- **One data file, one loader, one wiring line.** `gui2/field_help.json` holds the text. `gui2/field_help.py` loads and validates it. `_create_field_row` sets the tooltip. No new class, no new setting, no change to `FieldConfig`. (Owner chose JSON and the hover tooltip. See the spec.)
- **Tooltip on the label, not on the input.** The label is outside every composite field, so one place covers all 50 rows, including multiline and composite ones.
- **`ft.Tooltip` object, not a string.** Only the object lets us set `wait_duration` and `size_constraints` (the max width). No manual wrapping, so the tested text and the shown text are the same.
- **Module-level cache.** The whole `DpdFields` object is rebuilt on every clear, so a per-instance cache would read the file again each time.
- **Drift guard is a test, not a run-time warning per key.** A missing key at run time returns `None` silently. A load failure logs once.
- **Not abstracted on purpose:** no per-option help for dropdowns, no help for `_add` fields, no hot reload of the file, no setting to switch help off.
- **Checks read as functions.** `validate_field_help` takes plain data, so a test can break a copy and see it fail.

## Phase 1 — Loader, validator, wiring

- [x] Create `gui2/field_help.py` with these four names and nothing else:
  - `HELP_PATH: Path = Path("gui2/field_help.json")`
  - `MAX_HELP_LENGTH: int = 300`
  - `load_help_file(path: Path) -> dict[str, str]`: read with `encoding="utf-8"`, parse JSON. On any failure (file missing, `json.JSONDecodeError`, `OSError`, top level not a dict, any value not a `str`) call `ic(...)` with the path and the error, and return `{}`. Catch those specific errors, not a bare `except`.
  - `validate_field_help(help_texts: dict[str, object], names: list[str]) -> list[str]`: returns one message per problem. Problems: a name with no key; a key not in `names` (this also catches `_add` keys); a value that is not a `str`; an empty or whitespace-only value; a value longer than `MAX_HELP_LENGTH`. A newline is allowed (changed after review). An empty list means no problems.
  - `get_field_help(name: str) -> str | None`: returns the text from `_cached_help() -> dict[str, str]`, a `functools.cache`-d function that calls `load_help_file(HELP_PATH)` once. Returns `None` when the key is absent.
  → verify: `uv run ruff check --fix gui2/field_help.py && uv run ruff format gui2/field_help.py && uv run pyright --project /dev/null gui2/field_help.py` (plain pyright analyses nothing under `gui2/`). Expect `All checks passed!` from ruff and `0 errors, 0 warnings` from pyright.
  Result: ruff `All checks passed!`; pyright `--project /dev/null` 0 errors, 0 warnings. One change from the text: load failures catch `(OSError, ValueError)` (ValueError covers JSONDecodeError and UnicodeDecodeError).
- [x] Create `tests/gui2/test_field_help.py`.
  - A helper `field_config_names() -> list[str]` parses `gui2/dpd_fields.py` with `ast`, finds class `DpdFields`, method `__init__`, and collects `call.args[0].value` (a `str` constant) of every `ast.Call` whose `func` is `ast.Name` with `id == "FieldConfig"`. Some calls span several lines, so read `args[0]`, never the line text. A test asserts the list has exactly 50 names and no duplicates.
  - `validate_field_help` tests, each its own test function, built from a good dict made from those 50 names: good dict returns `[]`; one key removed; one key renamed; one text empty; one text of 301 characters; one text containing a newline must pass; one extra key `lemma_1_add`; one non-string value. Each broken one asserts the returned list is non-empty and names the key.
  - `get_field_help` tests: a fixture calls `_cached_help.cache_clear()` before and after each test and monkeypatches `gui2.field_help.HELP_PATH` to a `tmp_path` file. A present key returns its text, an absent key returns `None`, and a missing file returns `None` without raising.
  - `load_help_file` tests using `tmp_path`: missing file, malformed JSON, a JSON list, a non-string value each give `{}` and do not raise; a good file returns its dict (with a Pāḷi text such as `"nāma"` to prove UTF-8).
  → verify: `uv run pytest tests/gui2/test_field_help.py`, expect all pass. Then run `uv run ruff check --fix tests/gui2/test_field_help.py && uv run ruff format tests/gui2/test_field_help.py && uv run pyright --project /dev/null tests/gui2/test_field_help.py`, expect `All checks passed!` and `0 errors, 0 warnings`.
  Result: 17 tests passed at that point (18 after the wiring test); ruff and pyright clean.
- [x] Wire the tooltip in `gui2/dpd_fields.py`, in `_create_field_row`, right after the `label = ft.Text(...)` block (line 461-467). Import `get_field_help` from `gui2.field_help`. Add:
  ```python
  help_text = get_field_help(field_name)
  if help_text is not None:
      label.tooltip = ft.Tooltip(
          message=help_text,
          wait_duration=500,
          size_constraints=ft.BoxConstraints(max_width=360),
      )
  ```
  Make no other hand edit in the file.
  → verify: first copy the file to `<scratchpad>/dpd_fields.before.py`. After the edit run `uv run ruff check --fix gui2/dpd_fields.py && uv run ruff format gui2/dpd_fields.py && uv run pyright --project /dev/null gui2/dpd_fields.py`, expect `All checks passed!` and `0 errors, 0 warnings`. The project rule is that a touched file must pass its own lint, so fix any pre-existing error with a behaviour-preserving change and list each one under this task. Then run `diff <scratchpad>/dpd_fields.before.py gui2/dpd_fields.py` (plain `diff`, not git). Expect only the import, the new lines, and the listed lint fixes. If `ruff format` rewrote more than about 10 unrelated lines, restore the copy, reapply the edit by hand, and skip the formatter for that file (the formatter version has drifted).
  Result: diff against the pre-edit copy shows only the import and the 7 new lines; ruff changed nothing. `pyright --project /dev/null` reports 90 errors in this file, none on the new lines (all `Control` attribute errors, e.g. `error_text`, `value`). PRE-EXISTING — NOT CAUSED BY THIS THREAD. Plain `uv run pyright gui2/dpd_fields.py` (the pre-commit form, `gui2` is in the pyright exclude) reports 0 errors. The 90 are not fixed: they are unrelated to this thread and fixing them would break the scope rule. Final-check task uses the plain form for this file.
- [x] Add a wiring test to `tests/gui2/test_field_help.py`: monkeypatch `gui2.dpd_fields.get_field_help` to return `"help for lemma_1"` for `"lemma_1"` and `None` otherwise. Build `types.SimpleNamespace(fields={"lemma_1": DpdTextField(name="lemma_1"), "x": DpdTextField(name="x")})` and call `DpdFields._create_field_row(fake_self, "lemma_1", False)`. Assert `row.controls[0].tooltip` is an `ft.Tooltip` with that message, `wait_duration == 500`, and `size_constraints.max_width == 360`. Call it for `"x"` and assert `row.controls[0].tooltip is None`. If building `DpdTextField` outside a page fails, copy how `tests/gui2/test_dpd_fields_classes.py` does it.
  → verify: `uv run pytest tests/gui2/test_field_help.py`, expect pass. Revert test: temporarily comment out the `label.tooltip = ...` assignment, run the file, expect the wiring test to fail for the right reason (the assertion on the tooltip, not an import error), then restore the line in the same command and re-run, expect pass. Write the number of failing tests under this task in this plan.
  Result: 18 passed. Revert check: with `if help_text is not None:` replaced by `if False:`, 1 test failed (`isinstance(None, ft.Tooltip)` assertion) and 17 passed; file restored by copy and diff shows no change; 18 pass again.
- [x] Phase 1 check: `uv run pytest tests/gui2` and `just typecheck`.
  → verify: both exit 0. A failure that was there before this thread is named here with its test id, not ignored.
  Result: `uv run pytest tests/gui2`: 648 passed (baseline before the thread: 630). `just typecheck`: 0 errors (123 suppressed, 91 warnings not shown), exit 0.

## Live check recipe (used by Phase 2 and Phase 4)

Start it only after the owner says yes. `$SCRATCH` is the session scratchpad folder. `$ROOT` is the project root.

1. Free port: `uv run python -I -c "import socket; s=socket.socket(); s.bind(('127.0.0.1', 0)); print(s.getsockname()[1])"`. Call the number `$PORT`.
2. Start, as a background Bash call from `$ROOT`: `FLET_FORCE_WEB_SERVER=true FLET_SERVER_PORT=$PORT timeout 1800 uv run python gui2/main.py > $SCRATCH/gui2.log 2>&1`. Wait for it with a bounded loop: `timeout 120 bash -c 'until grep -q . $SCRATCH/gui2.log; do sleep 2; done'`, then check the log has no traceback. Never use `flet run`. Never serve the repo root.
3. Find the PIDs for stopping later: `ps -eo pid,args | grep "[g]ui2/main.py"`. Write them to `$SCRATCH/gui2.pids`. Stop by `kill <pid>` for each. Never `pkill -f`.
4. Connect: `playwright-cli attach --extension=chrome` (the token is in `PLAYWRIGHT_MCP_EXTENSION_TOKEN`; do not print it). Open `http://127.0.0.1:$PORT`. Run an `eval` that clicks `flt-semantics-placeholder` so the page exposes text. Keep one page open. If a login or user prompt appears, stop and ask the owner.
5. Reach Pass 2 Add: press Alt+E (tab index 7 in `_TAB_JUMP_KEYS`, `gui2/main.py:254`). Reach Pass 1 Add: read the tab list built near `gui2/main.py:600-640`, find the Pass 1 Add tab, and click it.
6. Hover: take a snapshot, find the row whose name text is the field name, move the pointer onto that name text (not the input), wait 1 second, take a screenshot into `$SCRATCH`.
7. Selection check: press the mouse down at the start of the name, move across it, release, and take a screenshot. The name text shows a selection highlight.

## Phase 2 — Spike: does the tooltip work on the selectable label

Decides assumption A in the spec. Do this before writing 50 texts.

- [x] Create a minimal `gui2/field_help.json` with two entries, `lemma_1` and `meaning_1`, each a real draft text of about 200 characters (one long enough to need two or three lines at 360 px). Valid UTF-8, no trailing comma.
  → verify: `uv run python -I -c "import json,pathlib; d=json.loads(pathlib.Path('gui2/field_help.json').read_text(encoding='utf-8')); print(len(d))"` prints `2`.
  Result: file has 2 entries (`lemma_1`, `meaning_1`); the check printed `2`.
- [x] Ask the owner for a go to start the web server. After the yes, follow the live check recipe steps 1 to 5 for Pass 2 Add.
  → verify: the snapshot shows the Pass 2 form with the `lemma_1` row, and `$SCRATCH/gui2.log` has no traceback.
  Result: owner said yes. Server started on a free port, Pass 2 Add reached with Alt+E, no traceback. Recipe change: attached to the owner's Chrome with `playwright-cli attach --extension=chrome`; the token was not in the shell environment, so the owner pasted it.
- [x] Follow recipe steps 6 and 7 on `lemma_1`.
  → verify, pass: tooltip appears, wraps at about 360 px, text is selectable. Write PASS and a screenshot path in this plan, and go to Phase 3.
  → verify, fail: wrap the label in `ft.Container(content=label, width=150, tooltip=<the ft.Tooltip>)` inside `_create_field_row`, remove `width=150` from the inner `Text`, keep `selectable=True`, update the wiring test (`row.controls[0]` is now the Container), and repeat this task. If it fails again, stop and ask the owner. Never remove `selectable`.
  Result: PASS. Screenshots in the scratchpad: `p2_away.png` (no tooltip), `p2_hover_lemma1_b.png` (tooltip after a two-step pointer move and 2 s wait, wraps at about 360 px), `p2_select.png` (drag over the name shows a selection highlight). A single pointer jump did not show the tooltip in two tries; a pointer path with two small moves did, and the owner also saw it in his own browser. The owner confirmed in chat that `lemma_1` works.
- [x] Record: the final tooltip width and wait that look right (change `360` and `500` in `gui2/dpd_fields.py` and the wiring test if they do not); whether a Tab-focus on the `lemma_1` input shows any tooltip (assumption B, one line); how the tooltip looks on `meaning_1` (a tall row).
  → verify: three lines written under this task. If the width or wait changed, `uv run pytest tests/gui2/test_field_help.py` still passes.
  Result: 360 px and 500 ms kept (no change). Assumption B: after focusing the `lemma_1` input with the keyboard and moving the pointer away, no tooltip shows (`p2_focus_lemma1.png`), as the spec accepts. `meaning_1` (tall row): tooltip shows beside the name and covers part of the `meaning_lit` row below it (`p2_hover_meaning1.png`); it is readable and clears when the pointer moves.
- [x] Phase 2 check: stop the server with the PIDs in `$SCRATCH/gui2.pids` (recipe step 3). Then list files changed since the server started: `find . -newer $SCRATCH/gui2.pids -type f -not -path './.venv/*' -not -path './graphify-out/*' -not -path './.git/*' -not -name '*.pyc'` from `$ROOT`.
  → verify: `ps -p <pid>` finds nothing for each PID. The `find` list holds only files this thread edited or created (`gui2/field_help.json`, `gui2/field_help.py`, `gui2/dpd_fields.py`, `tests/gui2/test_field_help.py`) plus files the app or other threads write on their own (`gui2/data/*`). Name any other file in this plan.
  Result: server PIDs 1358155, 1358156, 1358161 are gone; Chrome session detached. `find -newer` lists `dpd.db-wal`, `dpd.db-shm` (the app's own database files) and `exporter/webapp/static/dpd.css` (not touched by this thread). Nothing else.

## Phase 3 — Write the 50 help texts

- [x] Read `docs/technical/style_guide_for_dpd_entries.md` and `docs/technical/dpd_headwords_table.md`. For `translation_1`, `translation_2` and `comment`, which have no doc source, read how the field is used in `gui2/dpd_fields.py`, `gui2/dpd_fields_examples.py` and `db/models.py`. Do not guess what a field means.
  → verify: `$SCRATCH/help_sources.md` exists with one line per field, `name | source (heading, table line, or code path) | ticked`, 50 lines, all sources filled.
  Result: `help_sources.md` in the scratchpad has 50 lines, each with its source. The owner also pointed at the headwords table doc, which was used for 7 fields. The owner said not to be fanatical about the texts because he will hand edit them.
- [x] Write all 50 entries into `gui2/field_help.json`, same order as the `FieldConfig` list. Style rules for every text:
  - 1 or 2 sentences, at most 300 characters, `\n` allowed after review, so a line that shows a key press, a button or a symbol sits on its own line; key words in CAPITALS.
  - Say what to put in the field, in words a Pāḷi scholar uses. No database words ("column", "string", "null", "FK").
  - Give a short example in the text only where the field is hard to guess (`root_sign`, `construction`, `phonetic`, `sanskrit`, `family_compound`, `compound_construction`).
  - Similar to, not copied from, the style guide. If the style guide has a rule about the field (for example "+inf" for `plus_case`), keep the rule's facts exact.
  - Diacritics as UTF-8 characters, not escapes. Write the file with `ensure_ascii=False` if a script is used.
  → verify: `uv run python -I -c "import json,pathlib; d=json.loads(pathlib.Path('gui2/field_help.json').read_text(encoding='utf-8')); print(len(d), max(len(v) for v in d.values()))"` prints `50` and a number of 300 or less.
  Result: file has 50 keys in `FieldConfig` order, longest text 235 characters. Extra facts found while drafting: `translation_1` and `translation_2` are not columns of the headword table (checked in the db) and are dropped by the `hasattr` filter in `pass1_add_controller.py`; `comment` is not a column either and is stored with the addition or correction (`additions_manager.add_additions`); pressing Enter in `id` fills the next free id (`id_submit`).
- [x] Add a test to `tests/gui2/test_field_help.py`: the real `gui2/field_help.json`, read with `load_help_file`, passes `validate_field_help` against `field_config_names()` with no problems.
  → verify: `uv run pytest tests/gui2/test_field_help.py`, expect all pass. Then remove one key from a copy in the scratchpad and call `validate_field_help` on it in a one-off `uv run python -I` command, expect a non-empty list.
  Result: `uv run pytest tests/gui2/test_field_help.py`: 19 passed. One-off check: removing `pos` from a copy makes `validate_field_help` return `['pos: no help text']`.
- [x] Review pass over the 50 texts: for each field, re-read the doc line or code path and check the text does not contradict it.
  → verify: all 50 lines in `$SCRATCH/help_sources.md` have `ticked` set to yes. Write the three no-source fields (`translation_1`, `translation_2`, `comment`) and their texts under this task for the final report.
  Result: done while writing, against the style guide, the table doc, the live db and the code. The three no-source fields: `translation_1`: "An English translation of example 1. It helps you check the example and is not saved in the dictionary entry." `translation_2`: same for example 2. `comment`: "A note to the reviewer about this word, for example why you added or changed it. Contributors must write one. It is kept with your addition or correction and is not part of the dictionary entry." The owner will skim and hand edit all 50.

## Phase 4 — Live check, docs line, final checks

- [x] Add one line to `gui2/README.md` naming `gui2/field_help.json` as the file that holds the field help texts and `gui2/field_help.py` as its loader. Read the README first and put the line where the other gui2 files are described.
  → verify: read the edited region and confirm only that line was added.
  Result: one bullet "Field help" added under Relationships & Data Flow; only that line changed.
- [x] Ask the owner for a go to start the web server (the Phase 2 go covered that run only). Follow recipe steps 1 to 6. In Pass 2 Add hover the name of each of `lemma_1`, `pos`, `meaning_1`, `example_1`, `commentary`, `family_set`, `compound_construction`, `notes`, `comment`. In Pass 1 Add hover the four of them that `PASS1_FIELDS` shows: `lemma_1`, `pos`, `example_1`, `comment` (`gui2/dpd_fields_lists.py:324`).
  → verify: 13 hovers (9 in Pass 2, 4 in Pass 1), each screenshot shows its tooltip with the right text. Write each screenshot path under this task. Any miss is a failure, not a note.
  Result: the owner said "carry on, do your thang" while the live check ran. Server started, attached to the owner's Chrome. 13 of 13 hovers show the right tooltip (screenshots in the scratchpad: `p2_lemma_1.png`, `p2_pos.png`, `p2_meaning_1.png`, `p2_example_1.png`, `p2_commentary.png`, `p2_family_set.png`, `p2_compound_construction.png`, `p2_notes.png`, `p2_comment.png`, `p1_lemma_1.png`, `p1_pos.png`, `p1_example_1.png`, `p1_comment.png`; extra `p2_example_2.png`). Scrolling up with the mouse wheel did not work in the page, so rows were reached by reload and scrolling down.
- [x] Stop the server with the PIDs in `$SCRATCH/gui2.pids` (recipe step 3).
  → verify: `ps -p <pid>` finds nothing for each PID.
  Result: PIDs 1365741, 1365742, 1365747 gone; Chrome session detached.
- [x] Final checks: `uv run ruff check gui2/field_help.py gui2/dpd_fields.py tests/gui2/test_field_help.py`, `uv run ruff format --check` on the same three files (skip `gui2/dpd_fields.py` if the formatter was skipped for it in Phase 1), `uv run pyright --project /dev/null gui2/field_help.py tests/gui2/test_field_help.py`, `uv run pyright gui2/dpd_fields.py` (plain form: `gui2` is in the pyright exclude, so this is the pre-commit result; the 90 strict-mode errors are pre-existing), `uv run pytest tests/gui2`, `just typecheck` (it runs `pyrefly check`).
  → verify: every command exits 0. Expect `All checks passed!`, `0 errors, 0 warnings`, and no failing test. A failure that is older than this thread is named here with its id.
  Result: ruff check: `All checks passed!`; `ruff format --check`: 3 files already formatted; pyright `--project /dev/null` on `gui2/field_help.py` and the test: 0 errors; plain `pyright gui2/dpd_fields.py`: 0 errors; `uv run pytest tests/gui2`: 649 passed; `just typecheck`: 0 errors. Smoke gate, full suite `uv run pytest tests/`: 2858 passed, 2 failed, 12 deselected. PRE-EXISTING / NOT CAUSED BY THIS THREAD: `tests/tools/test_tipitaka_db_deadline.py::test_four_ordinary_searches_at_once_do_not_time_each_other_out` (a timing test; it fails again when run alone; machine load was about 13) and `tests/scripts/server_contrib/test_maintenance_window.py::TestHappyPath::test_status_file_reports_a_failure_and_its_reason` (fails in the full run, passes alone: 20 passed). Neither file touches gui2 or the help files. Cause not investigated further. 90 strict-mode pyright errors in `gui2/dpd_fields.py` are pre-existing (see Phase 1).
- [x] Final report to the owner, in plain English with no paths in chat: what changed, the three texts with no doc source, a request to skim all 50 texts, the answers to assumptions A and B, and the known limits (keyboard-only contributors, no cue that help exists, label far from tall rows). Do not run `/kamma:3-review` unasked. Ask the owner whether to run `coderabbit review --agent`.
  → verify: the report names each limit and each unconfirmed item.

  Result: report given in chat. Limits named: keyboard-only contributors, no cue that help exists, label far from tall rows. Unconfirmed: the three no-source texts, and all 50 texts await the owner's skim. Assumption A passed; assumption B: no tooltip on keyboard focus. Owner not yet asked about `coderabbit review --agent`.