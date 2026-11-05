# Gate 2: review of the spec (2026-11-05)

Backend: pi, provider `deepseek`, model `deepseek-flash`, thinking off, tools read, grep, find, ls, no session. Two Goldfish, run one at a time (14:58 to 14:59). Raw reports: `raw/gate2_comprehension.md`, `raw/gate2_design.md`. No backend switch.

Finding ids: GC comprehension reviewer, GD design critic.

## Facts checked before deciding

- `rollback = _capture_rollback(config)` sits after two early `return`s that both set `Outcome.FAILED` (`maintenance_window.py` ~387-395), so `rollback` can be unbound in the `finally`. The spec now builds the path from `config`.
- `reconcile_all` (`contrib_reconcile.py` ~178-203) reads and writes only contributor files; the file has no reference to `dpd.db` or sqlite. Only the rebuild steps change the database.
- `build_shortcuts_dialog` has one caller, the Alt+? branch (`gui2/main.py:362`).
- `_reset_to_default_clicked` (`filter_tab_view.py` ~771-830) falls back to values typed in again, not to the constructor arguments.
- Button lines vs handler lines: Roots button `roots_tab_view.py:177`, handler `:293`; Infl button `inflection_templates_tab_view.py:426`, handler `:843`; DB tab button `filter_component.py:174`, handler `:426`.
- The DB tab is built in `main.py:188` as `FilterTabView(self.page, self.toolkit)`; its constructor defaults are `[("root_key", ""), ("family_root", "")]` and `["id", "lemma_1", "meaning_1", "meaning_lit", "root_key", "family_root"]`.

## Dispositions (17 findings)

| Id | Severity | Decision | How checked | Where fixed |
| :--- | :--- | :--- | :--- | :--- |
| GC1 | Blocker | Accept: path built from `config`, no `rollback` variable | read `run_maintenance` | spec 8 |
| GC2 | Major | Reject: `reconcile_all` never touches the database | read `contrib_reconcile.py` | spec 8 (reason written in) |
| GC3 | Major | Accept: rule and the known hit are written out | read `config_server.template` | spec 4 |
| GC4 | Major | Accept: each button and handler named by line | read the three views | spec 9 |
| GC5 | Major | Accept: filter shape and exact values given | read `filter_tab_view.py` | spec 10 |
| GC6 | Nit | Accept: keep rollback and the print for other errors, written out | read code | spec 3 |
| GC7 | Nit | Reject: the 30 and 10 runs are the time box; `plan.md` is written in this run | none | none |
| GC8 | Nit | Accept: exact messages at both sites | read `pass2_add_view.py` | spec 1 |
| GD0 | Nit | Accept: button sites and handler sites separated | read the three views | spec 9 |
| GD1 | Blocker | Accept the unbound variable and the early returns (as GC1); reject "unknown state after a failed restart" (the copy is only for a failed rebuild) | read code | spec 8 |
| GD2 | Blocker | Reject: SQLite fixes the text and SQLAlchemy keeps it in `str(exc)`; a type check adds nothing; an INFO log defeats the purpose. Accept: the test uses a real read-only file | read code | spec 3 |
| GD3 | Major | Accept: guard every `e.alt` test through one local variable | read `on_keyboard` | spec 11 |
| GD4 | Major | Reject: the popup opens only from the Alt+? branch (one caller) | rg `build_shortcuts_dialog` | spec 11 (fact written in) |
| GD5 | Major | Accept: Reset uses the constructor values | read `_reset_to_default_clicked` | spec 10 |
| GD6 | Major | Accept: exact branch written in `main` | read `main` | spec 7 |
| GD7 | Nit | Reject as a cause (the test runs in milliseconds, at 07:14); accept keeping the log file name and text | read the test | spec 12 |
| GD8 | Nit | Accept (as GC8) | read code | spec 1 |

## Counts

Counted from the table by the first word of each Decision cell: 17 findings, 12 accepted (GD1 in part), 5 rejected (GC2, GC7, GD2, GD4, GD7; GD2 and GD7 each have a small accepted part, written in the table), 0 escalated.
