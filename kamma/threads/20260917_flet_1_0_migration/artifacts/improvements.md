# Structural improvements taken during the migration

Rule and boundary: `spec.md` → *Structural improvement — the rule*.

Short version: an improvement is allowed only in code the migration is already
rewriting, must be invisible in the wiring diff and the behaviour catalogue, and
must be separable from the migration in the diff. Everything taken is logged
here. **An improvement not in this log is a review finding.**

**This log is the rollback mechanism.** The user commits everything at the end,
so improvement and migration land in one commit; separation therefore comes from
this file, which maps every improvement to the BR item that opened it and to
specific call sites. Rollback is "revert these named hunks", not "revert that
commit".

Two requirements follow: **sequence migration edits before improvement edits per
file**, and **never mix a restructure into the same hunk as a rename or an API
fix** — a hunk doing both cannot be reverted on its own, which defeats the
mechanism.

**When in doubt, preserve current behaviour.** That is the thread's standing
rule and it decides candidates without a round trip: C10 was rejected on it.

## Log

One row per improvement, filled in as they are taken.

| # | What changed | Opened by | Evidence behaviour is identical |
|---|---|---|---|
| 1 | `field_border()` in `gui2/ui_utils.py` replaces the `ft.OutlineInputBorder(border_radius=…, side=ft.BorderSide(…))` expression that BR-22 would otherwise have spelled out 112 times. One place now states the editor's field radius. | BR-22 | Every call's arguments were derived mechanically from the kwargs it replaced (`artifacts/check_border_props.py` before/after: 116 deprecated kwargs → 0). Colour omitted where the old code omitted it, so the theme still resolves the per-state colour. |
| 2 | `cell_border(colour)` in `gui2/filter_component.py` — the grid cell's square 3px border in one place, used by both the constructor and the spell check. | BR-22 | The spell check previously set only `border_color`, inheriting the cell's radius and width; routing it through `cell_border` reproduces exactly that shape, which a bare `field_border(color=RED)` would not have. |

---

## Candidates

Found while cataloguing. **Not approved — each still has to pass the three
questions at the time its file is opened.** Listed so the opportunity is not
missed when the phase arrives, and so a later agent does not have to rediscover
them.

### ~~C1~~ — resolved, and it is not an improvement

**Settled 2026-09-17 after review. C1 was listed on a false premise.**

Revision 7 assumed the 23 classes read `self.page` during `__init__`, making the
fix per-view design work that wanted a shared pattern. AST-checked across all 23
`__init__` bodies and every method they call on `self`:

- direct `self.page` reads inside `__init__`: **0**
- `__init__`-called methods that read `self.page`: **2**, both
  `_update_history_dropdown` (`pass1_add_view.py:432` via `:227`,
  `pass2_add_view.py:675` via `:268`), each ending `self.page.update()`

All 23 assignments are **store-only**. So the pattern is:

1. delete the assignment line, all 23, nothing else;
2. leave every handler-time `self.page` read alone — the 1.0 read-only property
   resolves once mounted, which is the only time handlers run. No `self._page`
   mirror (it can go stale; the property cannot), and no rewriting of the ~1,000
   runtime uses;
3. parameterise the two real sites — pass the page into
   `_update_history_dropdown` from constructor scope. Not `did_mount`: that
   moves *when* the work happens, and `pass2_add_view.py:936` already calls the
   same method from a handler where `self.page` is correct;
4. expect pyright noise (1.0 types `.page` optional) — lint, not design.

**That is the BR-17 fix, not an improvement on top of it**, so it belongs in the
plan's BR-17 task and not in the taken-improvements table above. Kept here as
the record of why the pattern is what it is.

### Opened by BR-14 (`gui2/main.py` tab machinery)

**C2. The tab index is currently carried by four parallel structures** —
`tab_labels`, `_TAB_JUMP_KEYS`, `_view_builders`, `_mounted_tabs`, plus
`self.tabs.tabs[i]` — and 1.0 adds a fifth (`TabBarView.controls[i]`) in place
of the per-`Tab` `content` slot. The migration is rewriting the indexing; a
single keyed structure would remove the class of bug where one list drifts from
another.

Behaviour check: all 16 tabs, original order and labels, each building on first
selection and not rebuilt on the second; arrow-key and Alt-jump navigation
including past both ends; `_tab_label()` returning a name; Ctrl+S saving.

**C3. `_tab_label()` reads the label back out of a control** (`:355-356`,
`getattr(tab_content, "value", None)`), when `tab_labels` at `:365` already holds
the strings. Reading the source list is both simpler and immune to BR-14's
`Tab.label` change.

Behaviour check: the same string appears in the same messages.

### Opened by BR-14 (`gui2/main.py`, the warm-up worker)

**~~C10~~ — REJECTED 2026-09-17. Preserve current behaviour.**

`_warmup_in_background` (`:328-338`) catches every builder exception and keeps
only the tab label, discarding the cause:

```python
except Exception:
    failed.append(self._tab_label(index))
```

This is why BR-17 presents as silence rather than an error, and improving it was
tempting. It is still **not taken**: changing what a failure path reports is a
change to observable behaviour, and this thread preserves behaviour. It also
fails question 1 — BR-14 rewrites `_tab_label` and `_ensure_tab_built`, but not
the `except` line itself.

**Consequence to carry forward, not to fix:** BR-17's verification cannot be
"the app starts". It is the **"All tabs and tools ready." snackbar plus opening
every tab** — already written into spec BR-17 and the plan's BR-17 task. The bad
error reporting stays; the verification works around it.

Worth its own thread later, with the swallowed-exception rule in the project
conventions as the justification.

### Opened by Phase 4 (handlers being offloaded)

**C4. `CompoundTypeManager` is constructed inside `construction_blur`**
(`dpd_fields.py:1553`) and `PhoneticChangeManager` inside `phonetic_focus`
(`:913`) — each re-reads its TSV from disk on every blur/focus. Phase 4 is
touching both handlers to get the work off the event loop. Hoisting the manager
to a single instance is part of the same fix.

Caveat: the two `_click_edit_*` handlers open those TSVs for the user to edit,
so a hoisted instance must still pick up a file the user changed. Preserve that
or do not hoist.

Behaviour check: the compound-type suggestion and the phonetic suggestion still
appear, with the same values, including after the user edits the TSV.

**C5. `_search_and_fill_sanskrit` (`:997`) opens its own database session per
call**, and has four entry points (`sanskrit_focus`, `sanskrit_blur`,
`sanskrit_submit`, `non_ia_blur`) that repeat the same
`if not done and not value` guard three times between them. Phase 4 is rewriting
this call to get it off the event loop.

Behaviour check: the same Sanskrit string is produced for the same construction,
and the `sanskrit_done` flag still suppresses repeat searches. Note the four
entry points do **not** share identical guards today — `sanskrit_submit` forces
a search regardless of the flag. Preserve that difference; it is intentional.

**C7. `BoldDefinitionsSearchManager` is constructed inside
`click_commentary_search`** (`dpd_fields_commentary.py:203`), once per click.
Same shape as C4, same phase. Note `ToolKit` already holds a
`bold_definitions_search_manager` that `main.py` warms up at startup — so the
per-click construction is not just wasteful, it bypasses the warmed instance.
Check whether they are interchangeable before reusing it.

Behaviour check: the same results in the same order for the same search terms,
including the `MAX_SEARCH_RESULTS + 1` truncation and its amber notice.

**~~C8~~ — REJECTED 2026-09-17, fails the rule's own boundary.**
`_handle_last_control_blur` is duplicated between `dpd_fields_examples.py:315`
and `dpd_fields_commentary.py:158`, with the speech-marks logic under two
spellings of the name. But de-duplicating it means either a new shared module or
moving the logic into `SpeechMarkManager`:

- a new shared helper is a **module-boundary change**, explicitly out of scope;
- `SpeechMarkManager`'s file is **not opened by the migration**, so moving it
  there fails question 1.

Also the two copies are not identical — the examples version additionally saves
to the stash — so any merge carries behaviour risk for no in-scope gain.

**Disposition: `NOTICED — NOT TOUCHING`.** Phase 4 still gets the disk write off
the event loop in both places; it just does so twice, as the code stands.

### Opened by BR-7 / BR-17 (the pass views)

**C9. Pass2Pre and Pass2x-in-commentary are near-duplicates.** Both carry a
search bar, an exception field, a run button, the same four verdict buttons
(`handle_yes_click` / `handle_no_click` / `handle_new_click` /
`handle_pass_click`), the same `_handle_more_click` / `_handle_less_click`
paging, the same `handle_example_selection_change`, and the same inline `on_ok`
popup. Same method names in both files.

Both files are opened by BR-17 and by the `ElevatedButton` rename, so they are
already being edited throughout.

**~~C9~~ — PARKED 2026-09-17, out of scope for this thread.**

Sharing a base class between two pass views is a module-boundary change, which
the rule excludes, and question 2 is arguable: the two views are not identical
(Pass2Pre has two toggles Pass2x lacks, Pass2x has a word-in-text field Pass2Pre
lacks, and the verdict semantics differ), so the wiring diff and the catalogue
entries would not by themselves prove the merge safe.

Leaving it live invites a later agent to inherit an arguable candidate mid-
migration. **Disposition: park it as its own future thread**, to be scoped
properly against both views' behaviour rather than opportunistically during a
dependency upgrade. Recorded here so the observation is not lost.

### Opened by BR-13 (the `_add` field guard)

**C6. The transfer-button rebuild is duplicated.** `update_add_fields`
(`:523-550`) and `check_and_color_add_fields` (`:590-625`) both walk the field
row, find the `IconButton` by its `data` tag, set `disabled`, and reassign an
identical lambda. Two copies of the same 15 lines.

Only take this if BR-13's guard work actually opens these functions. If the
guard lands in `construction_blur` alone, this stays shut.

Behaviour check: the `←` buttons enable and disable at the same moments, and the
red/grey suggestion colouring is unchanged.

---

## Explicitly not candidates

- The `print()` debug calls at `dpd_fields.py:931,934,1565`. Project convention
  is `icecream`, but this is a convention fix in code the migration does not
  otherwise rewrite.
- The typo `"root_key and family_root dont's match"` (`:1157`). User-visible
  string, therefore a behaviour change, however trivial.
- The 45 `ft.dropdown.Option` sites, the two `ft.border.BorderSide` calls, the
  22 safe `self.page` assignments. Cosmetic renames, out of scope.
- `DpdFields.get_field` returning `""` for a missing field
  (`:666`, `self.fields.get(name, "")`) rather than `None`, which every caller
  then has to guard. Real, and a real trap — but it is a public shape used
  across the field system and the pass views, so changing it is a refactor
  thread of its own, not a migration improvement.
