Line claims all hold. Now the report.

## Goldfish review — `20261105_contrib_x_fixes/spec.md`

**Line-claim audit: all accurate.** Verified: pass2_add_view.py:1066/1344/1348; main.py:22/746/747/486-487/299-_TAB_JUMP_KEYS:254; database_manager.py:390-399/795; pass1_add_controller.py:8/48; contrib_pull.py:476/526/596; maintenance_window.py:288/373; filter_component.py:174/426-431; roots_tab_view.py:294/343; inflection_templates_tab_view.py:789/844/881; preview.py:170. Note main.py:746 is `start_dpd_server()`, the import is at :22, not "~746 and its import" — trivial.

**Minor correction:** item 9 claims the DB-tab Save button is at `filter_component.py:174` as `ft.Button("Save Changes", ...)`. It is. But item 9 also says Roots' Save is "~294" — :294 is `_save_root`'s guard, while the button is at :177. The spec conflates button sites with handler sites; an implementer grepping handler lines will disable nothing.

### Blocker

**1. Item 8 deletes the rollback copy before it might still be needed — outcome semantics unreconciled.** maintenance_window.py:397 captures the copy; :428-431 restores and sets FAILED; :432-435 catch failures *before* the pull (no rollback exists, `db_backup` may be None). The spec says delete in `finally` "when the outcome is not FAILED". But `Outcome` starts as SKIPPED (:383) and the two early `return` paths (:387-395, stop_failed / dirty tree) return with the copy never made — fine — whereas the outer `except` (:432) leaves outcome FAILED with no copy. The unhandled case: a *successful* rebuild that later fails inside `_write_status` or `_systemctl start` sets nothing, so the copy is deleted while the window's final state is unknown to the operator. The spec never states whether "not FAILED" means `Outcome.REBUILT` only. **Fix:** state the exact predicate (`outcome is not Outcome.FAILED`, and guard `rollback` possibly unbound), and say what happens when `_systemctl` start fails after deletion.

**2. Item 3's string match is a decision presented as fact.** Spec: "Do not print when the error message says `readonly database`". SQLite emits "attempt to write a readonly database" — but SQLAlchemy wraps it as `OperationalError`, and `.msg` casing varies across builds (`readonly` vs `read-only`). The spec forbids a probe, so the only signal is a brittle substring on `str(exc)`. Failure scenario: any driver wording change re-introduces the nightly print, or worse, a *different* sqlite error containing "readonly" is silently swallowed and the cache never refreshes on the primary. **Fix:** match on the exception type + `"readonly" in str(exc).lower()`, and log at INFO instead of suppressing entirely so the primary case stays diagnosable.

### Major

**3. Item 11 asserts `self.page.web` per-branch but never names which branches.** Reading main.py:299-385, the Alt branches are: arrows (:337,:343), X (:349), shortcuts popup (:355), tab jumps (:366). The spec's enumeration ("Alt+G T P E D S B R C I") is reconstructed from `_TAB_JUMP_KEYS` (:254) and is *not verified in the text* — the spec admits Alt+D/E/F "are from memory and unverified" yet still lists them as handled. The failure: an implementer guards only the listed keys and leaves a branch live in Chrome. **Fix:** say "guard every `elif` whose condition tests `e.alt`", not a key list, and drop the unverified keys.

**4. Item 11 interacts with Ctrl+S and the popup in a way the spec declares safe without evidence.** The spec says "Ctrl keys and page-scroll keys are untouched", but the popup (:355) is *also* built from `_shortcut_groups()` which reads `_TAB_JUMP_KEYS`; disabling Alt branches makes `_shortcut_groups` describe keys that no longer work in the browser. The spec says the popup "needs no other change" — that is a decision, not a finding, and it ships a popup listing dead keys. **Fix:** either filter the popup on `page.web` or state explicitly that a wrong list is accepted.

**5. Item 10's non-primary default contradicts item 10's own no-migration clause.** Only the *first* preset wins (`filter_tab_view.py:64`), so a contributor with any saved preset keeps it — but `_reset_to_default_clicked` (:767-774) also calls `get_first_preset()` and falls back to the *constructor* defaults. After the change, "Reset to Default" gives a contributor a root-keyed filter, not the starter. The spec is silent. **Fix:** resolve the reset path explicitly.

**6. Item 7 gives no text and no boundary for partially-skipped runs.** `_pull` sets the skip at :476 *before* any work; `run` sets it at :526 as one of three skip reasons (:519, :523, :526). The spec says "every time the outcome is exactly `skipped: editor open`" — good — but `main` (:596) currently guards with `not status.outcome.startswith("skipped")` and then calls `maybe_notify`. The implementer must invent whether the new notice bypasses that guard or nests inside it, and whether `status.notice_error` is still written. **Fix:** state the exact branch.

### Nit

**7. Item 12 is unfalsifiable as written.** "Run the test alone 30 times" — no wall-clock box, no seed control, no instruction to record the *command line* used. `_write_status` (:180-215) reads today's log file by date; `_setup(tmp_path)` gives a fresh `log_dir` but the log *filename* is date-stamped, so a run crossing midnight splits the log and naturally yields `problems: 0`. The spec rejects the "two runs" theory but never considers this one. **Fix:** add "check the timestamp of the log file against `maintenance window start`" to the investigation.

**8. Item 1's example message is inventable.** "for example 'lemma_1 not copied: clipboard blocked'" — the implementer must decide whether the string includes the exception, and whether `update_message` overwrites the save confirmation. Say it.
