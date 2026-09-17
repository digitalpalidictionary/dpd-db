# Spec — Flet 0.28.3 → 1.0.0 migration

**Thread type:** chore / major dependency migration
**GitHub issue:** none (do not create one)
**Date:** 2026-09-17
**Revision:** 8 — applies two independent reviews. Corrects the safe-site count
(28 → 22), corrects BR-17's fix approach (the constructors are store-only, so
the fix is far smaller than revision 7 claimed), re-derives the handler-density
table from the inventory, adds two BR-14 traps, narrows the improvement rule's
Phase 4 clause, and flags the rollback mechanism as needing a user decision.
Revision 7 added the structural-improvement rule: behaviour preservation
is absolute, structural preservation is not. Revision 6 rewrote the spec after
Phase 0, Phase 1 and Phase 2a completed and Phase 2b partially completed, adding
BR-14 to BR-17, correcting BR-1's count and BR-4's scope, and re-scoping Phase 3
from a rename pass to two rewrites plus a rename pass.

---

## Overview

`gui2/` (the DPD word-editing desktop app), the 7 `db_tests/gui/` helpers and
the 4 updater files are pinned to `flet[all]==0.28.3`. Flet 1.0.0 changes the
threading model, adds automatic updates, moves non-visual features to services,
and renames or removes a long list of controls, properties and constants.

Work happens on branch `flet-1-0` in the main working tree. The branch is not
merged in this thread; the user battle-tests it first.

**Reference material:** `artifacts/flet_1_0_migration_notes.md` holds the
migration guide and three companion breaking-change pages, tables verbatim.

**The installed wheel is the authority, not the guide.** The guide was written
against a release candidate. It is wrong about `Dropdown.on_change` (BR-1) and
buries `self.page` (BR-17) in a section this codebase would skip. Every claim
below was verified by importing `flet==1.0.0` in an isolated venv and
inspecting the classes.

---

## Verified facts

### Current state

| Fact | Value | Source |
|---|---|---|
| Pinned version | `flet[all]==0.28.3` | `pyproject.toml:61` |
| Target | `1.0.0`, requires Python `>=3.10` | PyPI + installed wheel |
| Project Python | `>=3.13,<3.14` | `pyproject.toml:6` |
| 1.0.0 on 3.13 | installs and imports | tested |
| `gui2/` size | 73 `.py` files, ~21,451 lines | `find` + `wc` |
| Handler bindings, `gui2/` | 415 (AST) / 454 (`rg`) | `artifacts/wiring_baseline.txt` |
| Handler bindings, repo-wide in scope | 463 across 96 files | same |
| `async def` in `gui2/` | 0 | `rg` |
| Manual `.update()` calls | 372 | `rg` |
| DB-touching call sites | 136 | `rg` |

The two handler counts measure different things and both are correct:

| Count | What it is |
|---:|---|
| 395 | `on_*` passed as a call keyword |
| 20 | `on_*` assigned onto a control (`page.on_keyboard_event = ...`) |
| 35 | `on_*` as a parameter in a `def` |
| 1 | a local variable named `on_tab_focus` (`gui2/main.py:314`) |
| 3 | commented-out code (`gui2/mixins.py:128,140,141`) |
| **454** | total textual hits in `gui2/` |

415 of those are bindings and are in the inventory.

Note: `rg -o 'on_[a-z_]+\s*='` returns **516**, not 454, because it matches
inside longer identifiers. Use `\bon_[a-z_]+\s*=`.

### Handler breakdown (repo-wide, from the inventory)

| Handler | Total | in `gui2` |
|---|---:|---:|
| `on_click` | 228 | 193 |
| `on_submit` | 69 | 69 |
| `on_change` | 59 | 53 |
| `on_blur` | 44 | 44 |
| `on_focus` | 34 | 34 |
| `on_hover` | 10 | 10 |
| `on_keyboard_event` | 9 | 6 |
| `on_complete` | 2 | 0 |
| `on_result` | 2 | 0 |
| `on_tap` | 2 | 2 |
| `on_blur_callback`, `on_delete`, `on_dismiss` | 1 each | 1 each |

Repo-wide, `rg -o '\bon_click\s*='` over the three scanned roots returns **230**
against the inventory's 228. The two extras are commented-out code at
`gui2/mixins.py:140,141` — the same block as two of the three commented hits in
the `gui2` table above.

### Handler density (top 12)

Re-derived from `artifacts/wiring_baseline.txt`, which is the declared authority.
Revisions 1–7 mixed AST and stale `rg` numbers in this table — `pass2_add_view`
49, `compound_type_tab_view` 31, `tests_tab_view` 18, `dpd_fields_examples` 25,
`dpd_fields_commentary` 20 and `dpd_fields_classes` 22 were all `rg` counts.

| File | Bindings |
|---|---:|
| `gui2/dpd_fields.py` | 96 |
| `gui2/pass2_add_view.py` | 37 |
| `gui2/compound_type_tab_view.py` | 27 |
| `gui2/filter_tab_view.py` | 21 |
| `gui2/dpd_fields_examples.py` | 20 |
| `gui2/pass1_add_view.py` | 17 |
| `gui2/sandhi_view.py` | 16 |
| `gui2/tests_tab_view.py` | 15 |
| `gui2/dpd_fields_commentary.py` | 14 |
| `gui2/pass2x/in_commentary_view.py` | 13 |
| `gui2/pass2_pre_view.py` | 13 |
| `gui2/dpd_fields_classes.py` | 11 |

---

## Breaking changes

Ordered by required work, largest first. All verified against the wheel.

### BR-17 🔴 `self.page = page` is not assignable on a control

In 0.28 `Control.page` is a writable attribute. In 1.0 it is a read-only
property:

```python
class Foo(ft.Column):
    def __init__(self):
        super().__init__()
        self.page = "x"
Foo()
# AttributeError: property 'page' of 'Foo' object has no setter
```

Raised at construction, so no view builds.

**23 sites, all inside `ft.Column` subclasses:**

| File | Line | Class |
|---|---:|---|
| `gui2/bold_search_view.py` | 45 | `BoldSearchView` |
| `gui2/compound_type_tab_view.py` | 32 | `CompoundTypeTabView` |
| `gui2/dpd_fields_commentary.py` | 39 | `DpdCommentaryField` |
| `gui2/dpd_fields_compound_construction.py` | 29 | `DpdCompoundConstructionField` |
| `gui2/dpd_fields_examples.py` | 148 | `DpdExampleField` |
| `gui2/dpd_fields_family_set.py` | 31 | `DpdFamilySetField` |
| `gui2/dpd_fields_meaning.py` | 29 | `DpdMeaningField` |
| `gui2/dpd_fields_notes.py` | 28 | `DpdNotesField` |
| `gui2/filter_component.py` | 112 | `FilterComponent` |
| `gui2/filter_tab_view.py` | 34 | `FilterTabView` |
| `gui2/global_tab_view.py` | 18 | `GlobalTabView` |
| `gui2/pass1_add_view.py` | 36 | `Pass1AddView` |
| `gui2/pass1_auto_view.py` | 26 | `Pass1AutoView` |
| `gui2/pass2_add_view.py` | 55 | `Pass2AddView` |
| `gui2/pass2_auto_view.py` | 24 | `Pass2AutoView` |
| `gui2/pass2_pre_view.py` | 30 | `Pass2PreProcessView` |
| `gui2/pass2x/in_commentary_view.py` | 32 | `Pass2xInCommentaryView` |
| `gui2/roots_tab_view.py` | 20 | `RootsTabView` |
| `gui2/sandhi_find_replace_view.py` | 19 | `SandhiFindReplaceView` |
| `gui2/sandhi_view.py` | 30 | `SandhiView` |
| `gui2/spelling_find_replace_view.py` | 19 | `SpellingFindReplaceView` |
| `gui2/tests_tab_view.py` | 46 | `TestsTabView` |
| `gui2/translations_view.py` | 18 | `TranslationsView` |

**22 further `self.page =` assignments are on plain classes and must not be
touched** — `App`, `ToolKit`, `DpdFields`, `AppBarUpdater`, `WordFinderPopup`,
`GuiTestManager`, `TestsTabController`, `UsernameManager`, `AiSearchWindow`,
both `gui2/utilities/` scripts, the 7 `db_tests/gui/` managers, and the
updater's `DPDUpdaterApp` (two assignments) / `MainWindow` / `SetupWizard`.
Those classes are not controls; `page` stays an ordinary attribute.

A textual find-and-replace over `self.page =` fixes 23 and breaks 22. Use
`artifacts/check_self_page.py`, which separates them by AST and exits non-zero
while any control-subclass assignment remains. The checker's own output is the
authority on both numbers.

(Revisions 6 and 7 said 28 here. That was a miscount, not a checker gap:
`test_manager.py:21` is a bare annotation `self.page: ft.Page` with no value,
correctly excluded by the checker. Corrected in revision 8.)

#### The fix is smaller than revisions 6 and 7 claimed

Those revisions said "each of these classes reads `self.page` during
`__init__`... per-view work". **That is wrong.** AST-checked across all 23
classes — every `__init__` body plus every method it calls on `self`:

| | Count |
|---|---:|
| direct `self.page` reads inside `__init__` | **0** |
| `__init__`-called methods that read `self.page` | **2** |

All 23 assignments are **store-only**. The two genuine pre-mount uses are both
the same method:

| Site | Called from | The use |
|---|---|---|
| `gui2/pass1_add_view.py:432` | `__init__` via `:227` | `_update_history_dropdown` ends with `self.page.update()` |
| `gui2/pass2_add_view.py:675` | `__init__` via `:268` | the same method, same last line |

So the pattern is:

1. **Delete the assignment line.** All 23, and nothing else.
2. **Leave every handler-time `self.page` read alone.** Handlers run only after
   mounting, and 1.0's read-only property resolves correctly then. Do **not**
   rewrite the ~1,000 runtime `self.page` uses across these files; do **not**
   add a `self._page` mirror, which can go stale where the property cannot.
3. **The two real sites take the page from constructor scope** — pass it into
   `_update_history_dropdown` as an argument. Not `did_mount`: moving the call
   changes *when* the work happens, which is behaviour, and
   `pass2_add_view.py:936` calls the same method from a handler where `self.page`
   is correct.
4. **Expect pyright noise, not design work.** 1.0 types `.page` as optional, so
   handlers in the 23 files may need asserts or guards. Lint, per the
   touch-a-file-own-its-lint rule.

`gui2/filter_component.py` already uses `did_mount` for its first query, so the
codebase applies that pattern where it is genuinely needed.

**It does not fail loudly, despite raising at construction.** `gui2/main.py:328`
builds all 16 views on a warm-up worker thread inside a bare `except Exception`
that keeps only the tab label and **discards the exception**. The label lookup it
calls (`_tab_label`, `:355`) is itself broken by BR-14 and runs inside that
except handler, so its `AttributeError` is uncaught and kills the warm-up thread
at the first failure.

Observable result before the fixes: the window opens, the first tab renders, and
neither the "Warm-up failed for: …" nor the "All tabs and tools ready." snackbar
appears. Tabs are then built on demand when clicked, where they raise again.

**"The app starts" is therefore not evidence BR-17 is fixed.** The evidence is
the "All tabs and tools ready." snackbar plus opening every tab.

### BR-14 🔴 The tab container is a rewrite

The guide's rename table lists `Tab.text` → `Tab.label`. This codebase uses
neither `Tab.text` nor the guide's container shape.

**Verified** by `dataclasses.fields`:

| Field used today | In 1.0? |
|---|---|
| `Tabs.tabs` | no |
| `Tabs.on_click` | no |
| `Tab.tab_content` | no |
| `Tab.content` | no |
| `Tab.text` | no |
| `Tab.label` | yes |

1.0's `Tabs` fields are `length`, `content`, `selected_index`, `on_change`.
Headers live in `TabBar.tabs`, bodies in `TabBarView.controls`.

**6 break sites in `gui2/main.py`:**

| Site | Code | Failure |
|---|---|---|
| `:386-404` | `ft.Tabs(tabs=[...], on_click=..., on_change=...)` | `TypeError`, two unknown kwargs |
| `:392-399` | `ft.Tab(tab_content=..., content=...)` | `TypeError`, both kwargs gone |
| `:289`, `:408` | `self.tabs.tabs[index].content = self._view(index)` | the lazy-build mount point; must become `TabBarView.controls[index]` |
| `:230-231` | `tab = self.tabs.tabs[...]` then `view = tab.content` | Ctrl+S save path. Fails **silently** — the `hasattr` checks below it miss, so Ctrl+S stops saving with no error |
| `:243` | `len(self.tabs.tabs)` | `AttributeError`; the bound check stopping Alt+Right walking off the end |
| `:355-356` | `.tab_content` then `getattr(..., "value")` | `AttributeError` in `_tab_label()`, used in user-facing messages |

`:389` binds both `on_click` and `on_change` to `_on_tab_activated`. Under 0.28
a click therefore fires the handler twice, and the `_mounted_tabs` guard absorbs
the duplicate. 1.0 has no `on_click` on `Tabs`, so it fires once. **Record the
0.28 double-fire as an observation before changing anything** — the single fire
afterwards is the preserved behaviour, not a regression, and an implementer who
notices the count change should not have to re-derive that.

`gui2/test_app.py:40,44` has the same shape.

#### Two traps for the implementer

**1. `Tabs.content` is a required positional argument.** Verified:
`ft.Tabs(length=2)` raises
`TypeError: Tabs.__init__() missing 1 required positional argument: 'content'`.
There is no post-construction assignment route equivalent to the old `tabs=`.

**2. An incomplete fix fails silently rather than raising.** Verified: assigning
an attribute a 1.0 control does not define is accepted — `tab.content =
ft.Container()` on a 1.0 `Tab` writes to the instance dict, reads back fine, and
never reaches the UI. So an implementer who rebuilds the constructor but leaves
the `self.tabs.tabs[i].content = …` mount idiom in place gets **no error** —
just permanently empty tabs, with `_mounted_tabs` already marking them built.
That is why the verification is "open every tab and confirm its view appears",
not "no exception".

16 tabs are built on demand via `_mounted_tabs` / `_view_builders`. The mount
target changes from a per-`Tab` `content` slot to an index in one
`TabBarView.controls` list. Preserve: `selected_index` driving the keyboard
handler (`:230-248`), the Alt+key jumps, and the current-lemma lookup.

### BR-1 🔴 `Dropdown.on_change` does not exist in 1.0

**Verified:** `ft.Dropdown(on_change=...)` raises
`TypeError: Dropdown.__init__() got an unexpected keyword argument 'on_change'`.
1.0's `Dropdown` has `on_select`, `on_text_change`, `on_focus`, `on_blur`,
`on_animation_end`, `on_size_change`.

- `on_select` — "Called when the selected item of this dropdown has changed."
  The replacement for 0.28's `on_change`.
- `on_text_change` — fires while typing in an editable dropdown. New.

The guide states `on_change` survives and also fires on typing. It does not
survive.

**11 `Dropdown` + `on_change` bindings, at 9 sites:**

| Site | Notes |
|---|---|
| `gui2/dpd_fields_classes.py:62` | `DpdDropdown`'s own `super().__init__` |
| `gui2/dpd_fields.py:326` | the fan-out feeding the wrapper |
| `gui2/dpd_fields.py:153` | `root_key` field config |
| `gui2/dpd_fields.py:199` | `derivative` field config |
| `gui2/compound_type_tab_view.py:80,96` | |
| `gui2/dpd_fields_family_set.py:35` | |
| `gui2/filter_tab_view.py:392` | preset dropdown |
| `gui2/pass1_add_view.py:84` | history dropdown |
| `gui2/pass2_add_view.py:198` | history dropdown |
| `gui2/roots_tab_view.py:38` | |

**Correction to revisions 1–5: the field-system blast radius is 2 fields, not
8.** There are 8 `field_type="dropdown"` configs, but most bind only `on_blur`:

| Dropdown `FieldConfig` | Handlers bound |
|---|---|
| `dpd_fields.py:105` (pos) | `on_blur` |
| `dpd_fields.py:126` (trans) | `on_blur` |
| `dpd_fields.py:153` (root_key) | `on_focus`, **`on_change`**, `on_blur` |
| `dpd_fields.py:199` (derivative) | **`on_change`** |
| `dpd_fields.py:214` (compound_type) | `on_blur` |
| 3 others (`neg`, `verb`, `plus_case`) | none |

`DpdDropdown` is built with `editable=True, enable_filter=True`, so the
`on_select` / `on_text_change` split is a per-field choice. **Default:
`on_select` only**, which preserves 0.28. The one open question is `root_key`,
whose handler shows the root's gloss — under 0.28 only on selection. Putting it
on `on_text_change` too would update while typing, which is a behaviour change;
the user decides.

The other 22 dropdown constructions bind no `on_change`:
`ai_search_window.py:48` (`on_focus`), `dpd_fields_examples.py:183`
(`on_blur`), and 20 binding nothing — including the 7 editable dropdowns in
`tests_tab_view.py` (lines 139, 149, 167, 177, 187, 204, 223). Repo-wide, 14 of
30 dropdown constructions are editable.

### BR-4 🔴 `scroll_to` is async; the keyboard handler pair must both convert

**Verified:** `Column.scroll_to`, `Row.scroll_to`, `ListView.scroll_to`,
`GridView.scroll_to`, `Page.scroll_to` are all coroutine functions in 1.0.

`gui2/main.py:260` calls `target.scroll_to(delta=..., duration=100)` from a
synchronous `on_keyboard_event` handler. In 1.0 that returns an un-awaited
coroutine: PageUp/PageDown stops scrolling, with a RuntimeWarning and nothing
visible to the user.

`page.on_keyboard_event` is bound in three places in `gui2/`, two of which swap
with the first at runtime:

| Site | Binding |
|---|---|
| `gui2/main.py:48` | `self.page.on_keyboard_event = self.on_keyboard` — the global handler, holds `scroll_to` |
| `gui2/pass2_add_view.py:1367-1368` | saves the current handler, installs `_eg_kb_handler` while the eg dialog is open |
| `gui2/pass2_add_view.py:1395-1397` | `_restore_eg_kb` puts it back on dismiss |

`_eg_kb_handler` (`:1360-1365`) calls the saved handler directly:
`self._eg_saved_kb(e)`. Once `on_keyboard` is `async def`, that returns an
un-awaited coroutine and global keyboard handling stops for as long as the eg
dialog is open.

Fix both: `on_keyboard` → `async def`; `_eg_kb_handler` → `async def` and
`await self._eg_saved_kb(e)`.

`ai_search_window.py:168` binds its own page's handler and never swaps with
main's. The same pattern in `db_tests/gui/main.py:149`,
`db_tests/gui/add_hyphenations.py:324`, `resources/dpd-updater/main.py:38` and
both `gui2/utilities/` scripts is Phase 6 scope; none call `scroll_to`.

Also note `scroll_to`'s `key=` renamed to `scroll_key=` (not used here).

### BR-13 🔴 `update()` now raises, and one instance is confirmed

**Verified** by reading `BaseControl.update` in the wheel:

```python
if hasattr(self, "_frozen"):
    raise RuntimeError("Frozen control cannot be updated.")
if not self.page:
    raise RuntimeError(f"{...} Control must be added to the page first")
```

Both were silent no-ops in 0.28. The frozen-control case is not in the guide.

**Confirmed instance.** `gui2/dpd_fields.py:408` creates a shadow `_add` field
for each of the 48 editor fields. `add_to_ui` mounts them only when
`include_add_fields=True`, and only Pass2Add passes it
(`pass2_add_view.py:715`). Pass1Add takes the default `False`
(`pass1_add_view.py:338`), so in Pass1Add all 48 `_add` controls exist in
`self.fields` but belong to no page.

| Handler | Call | Reachable in Pass1Add? |
|---|---|---|
| `construction_blur` (`:1571`) | `compound_type_add_field.update()` | **yes** — `construction` is in `PASS1_FIELDS` |
| `phonetic_focus` (`:929`) | `phonetic_add_field.update()` | no — `phonetic` is not in `PASS1_FIELDS` |

Blurring `construction` in Pass1Add raises. Fix at the call site by guarding on
the control being mounted; the update is correct in Pass2Add.

Hiding a field (`filter_fields:493`, `add_to_ui:422`) only sets
`field_row.visible = False`; the control stays mounted, so `update()` on a
hidden field is safe. Only the unmounted `_add` fields are affected — Phase 5
does not need to audit all 48 fields.

### BR-11 — merged into BR-14

Revisions 1–5 carried BR-11 ("Tabs split into three controls", 🟡, a rename).
Phase 0 showed it is a rewrite, not a rename. The number is kept as a pointer so
earlier references resolve; the content is BR-14.

### BR-7 🟠 `ft.ElevatedButton` is gone

`ft.ElevatedButton` does not exist; `ft.Button` has `content`, not `text`.
**136 sites across 24 files.**

### BR-8 🟠 Dialogs — four patterns, four fixes

`Page.open` and `Page.close` are gone. `Page.show_dialog` and `Page.pop_dialog`
exist and are **synchronous**, so **all 37 dialog sites** — the 35
`page.open`/`page.close` calls plus the two one-off patterns below — need no
async conversion.
(Only `show_drawer`, `close_drawer`, `push_route` are async.) `ft.SnackBar`
subclasses `DialogControl`. `ft.AlertDialog` keeps its `open` field.

| Pattern | Sites | Fix |
|---|---|---|
| `page.open(...)` | 21 across 14 files | `page.show_dialog(...)` |
| `page.close(...)` | 14 across 4 files | `page.pop_dialog()` |
| `page.snack_bar = ft.SnackBar(...)` | 1 — `gui2/translations_view.py:127` | attribute gone → `page.show_dialog(ft.SnackBar(...))`; also carries a stale `# type: ignore` to remove |
| `page.overlay.append(dlg)` + `dlg.open = True` | 1 — `gui2/pass1_auto_view.py:193-197`, cancelled at `:199+` | `page.show_dialog(...)` / `page.pop_dialog()` |

**`ft.AlertDialog`: 20 constructions across 15 files.** A raw grep reports 22;
the other two are a type annotation (`gui2/pass2_add_view.py:78`) and a
commented-out block (`gui2/mixins.py:131`). Do not migrate or count either.

`ft.SnackBar`: 11 **mentions** across 4 files, but only **3 constructions** —
`gui2/mixins.py:113` and `gui2/ui_utils.py:25` (both inside show-snackbar
helpers, so almost every snackbar in the app comes from one of these two) and
the direct one at `gui2/translations_view.py:127`. The other 8 mentions are
calls to the helpers and type references. Phase 3's verification should exercise
the **3 construction sites**, reached through whichever screens call the helpers.

### BR-9 🟠 `FilePicker` is a service with awaitable methods

`ft.FilePicker` subclasses `Service`. `get_directory_path`, `pick_files`,
`save_file`, `upload` are coroutine functions returning their result directly.
`on_result` and `ft.FilePickerResultEvent` still exist, but the awaitable form
removes the callback round trip. Services go in `page.services`, not
`page.overlay`.

**4 sites, 2 files:** `resources/dpd-updater/ui_setup.py:113,131-132` and
`ui_main.py:293,318-319`. Both handlers become `async def`.

### BR-6 🟠 `ft.app` is gone

`ft.app` raises `AttributeError`; `ft.run` exists, and `target=` is now `main`.

**7 sites:** `gui2/main.py:446`, `gui2/test_app.py:56`,
`gui2/ai_search_window.py:174`,
`gui2/utilities/sandhi_contraction_find_replace_gui.py:308`,
`gui2/utilities/find_words_with_examples.py:297`, `db_tests/gui/main.py:166`,
`resources/dpd-updater/main.py:107`.

### BR-5 🟠 Clipboard is an awaitable service

`Page.set_clipboard` / `get_clipboard` gone. `ft.Clipboard` is a `Service`;
`set` and `get` are coroutine functions. No synchronous alternative.

**2 sites:** `gui2/pass2_add_view.py:934,1180`. Both handlers become
`async def`.

### BR-2 🟡 `ft.border.all()` is gone; the module survives

`ft.border.all` → `False`, but the `ft.border` module still exists and
`ft.border.BorderSide` still resolves. `ft.Border.all` and top-level
`ft.BorderSide` both exist. Fails at render time, not import time.

9 `ft.border.*` sites across 4 files; **7 break**:

| Site | Call | Breaks? |
|---|---|---|
| `gui2/bold_search_view.py:92,151,349,352` | `ft.border.all(...)` | yes → `ft.Border.all(...)` |
| `gui2/filter_component.py:32` | `ft.border.all(...)` | yes |
| `gui2/wordfinder_popup.py:163` | `ft.border.all(...)` | yes |
| `gui2/wordfinder_widget.py:109` | `ft.border.all(...)` | yes |
| `gui2/filter_component.py:33,34` | `ft.border.BorderSide(...)` | **no** — leave alone |

`ft.border.BorderSide(1, ft.Colors.GREY_300)` constructs in 1.0 and returns a
`ft.BorderSide`. Rewriting those two is cosmetic and out of scope.

### BR-3 🟡 Alignment constants change case

`ft.Alignment.CENTER` and `ft.Alignment.TOP_LEFT` exist; `ft.Alignment.center`
and `top_left` do not. A prefix-only replace crashes.

**11 sites across 8 files:** `center` × 9; `top_left` × 2
(`gui2/bold_search_view.py:238,243`). One is inside a comment block
(`gui2/mixins.py:137`) — leave it.

### BR-10 🟡 Padding / border-radius modules gone

`ft.padding.all`, `ft.padding.symmetric`, `ft.border_radius.all` gone;
`ft.Padding.*` and `ft.BorderRadius.*` present. `Padding.symmetric` is
keyword-only: `symmetric(*, vertical=0, horizontal=0)`.

**23 padding sites across 10 files; 1 border-radius site.**

### BR-16 🟡 `InputBorder` is a class hierarchy; enum members deprecated

The enum members still resolve and construct, each emitting a
`DeprecationWarning` and returning the new class:

```
InputBorder.OUTLINE   -> OutlineInputBorder(side=None, border_radius=4, gap_padding=4.0)
InputBorder.UNDERLINE -> UnderlineInputBorder(side=None, border_radius=BorderRadius(4,4,0,0))
InputBorder.NONE      -> NoInputBorder()
```

`TextField.border_color`, `border_width`, `border_radius` all still exist, and
`ft.TextField(border=ft.InputBorder.OUTLINE, border_color=..., border_width=1)`
constructs. Removal is scheduled for 1.3.0.

**No code change required** for the 8 `ft.InputBorder.*` sites or the 35
`border_color` / 12 `border_width` sites.

Two rendering changes land regardless:
- a border with no explicit `side` now takes its colour from the Material theme
  per state; 0.28 always drew the enabled border black;
- an explicit `side` styles the enabled state only — the focused border no
  longer picks up `border_color`.

Four sites use border colour as a signal and must be checked visually:

| Site | Signal |
|---|---|
| `gui2/filter_component.py:487-495` | red border on invalid filter input |
| `gui2/dpd_fields_examples.py:583-587` | red border when an example exceeds 300 characters |
| `gui2/tests_tab_view.py:567-577` | red border on a failing test row |
| `gui2/dpd_fields_examples.py:191-193` | grey border on the book dropdown |

### BR-12 🟡 `flet.version.version` is gone

`flet.__version__` → `"1.0.0"`; `flet.version.__version__` → `"1.0.0"`;
`flet.version.version` → missing.

### BR-15 🟢 `Switch.label_style` → `label_text_style` — 0 sites

`Switch.label_style` absent, `label_text_style` present. All 60-odd
`label_style=` occurrences in `gui2/` are `TextField.label_style`, which
survives unchanged. The 8 `ft.Switch(...)` constructions
(`pass1_auto_view.py:73`, `pass2_auto_view.py:84`, `pass2_pre_view.py:132,137`,
`pass2_add_view.py:172,176`, `sandhi_find_replace_view.py:41`,
`spelling_find_replace_view.py:40`) bind no style.

Recorded so a later agent does not mistake the `TextField` sites for this
rename.

### Confirmed safe — swept, tested, no action

- `ft.dropdown.Option` — still works; `ft.dropdown.Option("x")` returns a
  `DropdownOption`. All 45 sites across 17 files stay. `ft.DropdownOption` is
  the new canonical spelling; renaming is cosmetic and out of scope.
- `ft.TextField` — keeps `on_change`, `on_focus`, `on_blur`, `on_submit`,
  `on_click`, and `label_style`. Only `Dropdown` lost `on_change`.
- `Chip.on_delete` — present (`compound_type_tab_view.py:286`).
- The `DpdTextField` / `DpdDropdown` / `DpdText` subclassing pattern works
  against 1.0's dataclass controls — **except for `self.page`, see BR-17**.
- `page.overlay` — still a property returning a control list. Only the
  service-in-overlay idiom moves.
- `page.services` — new, where services go.
- `page.controls`, `page.appbar`, `page.padding`, `page.bgcolor`, `page.window`,
  `page.views`, `page.theme`, `page.fonts`, `page.title`,
  `page.on_keyboard_event`, `page.loop` — all present.
- `page.run_thread`, `page.run_task`, `page.update` — present and sync.
- `ft.context.disable_auto_update` — present.
- `ft.Colors.GREY_800` / `GREY_500` — present.
- Swept to zero hits: `ft.UserControl`, `ft.ConstrainedControl`, `ft.colors.*`,
  `ft.icons.*`, `ft.margin.*`, `page.client_storage`, `page.launch_url`,
  `page.go`, `page.on_resized`, `SafeArea`, `on_scroll_interval`,
  `primary_swatch` / `primary_color`, non-underscored colour constants
  (`rg 'ft\.Colors\.[A-Z]+[0-9]+'`), `_async`-suffixed methods, pubsub, chart
  controls, `e.target`, `DragTarget`, `SegmentedButton`, `Icon(name=)`,
  `Card(color=)`, `Badge.text`, `Chip.click_elevation`, `BoxDecoration.shadow`,
  `canvas.Text.text`, `NavigationRail*`, `Pagelet`, `Cupertino*Action`.
- The justfile's `flet run -d` hot-reload recipe survives in the 1.0 CLI.

---

## Blocking call sites

### Known from the code structure

| Location | Blocking operation |
|---|---|
| `gui2/global_tab_view.py:103,123,131,152` | `subprocess.Popen` / `run` (LibreOffice, Anki) |
| `gui2/global_tab_view.py:128,138` | `time.sleep(3)`, `time.sleep(2)` |
| `gui2/pass1_auto_controller.py:33,424,431` | lock, retry sleeps |
| `gui2/pass1_file_manager.py:19` | lock |
| `gui2/database_manager.py:49,103,671,675` | two locks, a raw `threading.Thread` worker, sleep debounce |
| `gui2/main.py:39,298,416,417` | `threading.RLock`, three `page.run_thread` calls |
| `gui2/main.py:437` | `start_dpd_server()` — FastAPI at app startup |
| `gui2/filter_component.py:128,239` | lock, `page.run_thread` |
| `gui2/toolkit.py:46` | lock |
| `gui2/test_manager.py:178`, `gui2/tests_tab_controller.py:325,328` | `subprocess.Popen` |
| `gui2/ai_search_window.py:14,30` | `subprocess.Popen` |
| 136 sites across `gui2/` | synchronous SQLAlchemy queries and commits |

`page.run_thread` re-establishes page context inside the worker; a raw
`threading.Thread` does not. The risk in the detector-rebuild worker
(`database_manager.py:671`) is its `update()` calls, not its locks.

### Found by reading handler bodies (Phase 2b)

To be confirmed by the Phase 2c measurement, not assumed.

| Handler | Event class | Blocking work |
|---|---|---|
| `_search_and_fill_sanskrit` (`dpd_fields.py:997`) | focus / blur / submit | opens its own session, runs `lemma_1 LIKE '%part%'` per construction part — unanchored scan of a 2.26 GB db. Four entry points: `sanskrit_focus`, `sanskrit_blur`, `sanskrit_submit`, `non_ia_blur` |
| `family_word_change` (`:1196`) | **change** | fuzzy-match against every known word family, per keystroke |
| `pattern_change` (`:1657`) | **change** | fuzzy-match against every pattern; loads the pattern set on first use |
| `root_key_change` (`:1090`) | **change** | `db.get_root_string()` per keystroke |
| `construction_blur` (`:1553`) | blur | constructs `CompoundTypeManager` — re-reads its TSV every blur |
| `phonetic_focus` (`:913`) | focus | constructs `PhoneticChangeManager` — re-reads its TSV every focus |
| `_compute_and_write_synonyms` (`:1314`) | `meaning_1` blur | relationship detector |
| `_compute_and_write_phonetic_variants` (`:1370`) | focus | phonetic-variant detector |
| `click_book_and_word` (`dpd_fields_examples.py:344`) | submit | parses a CST book |
| `_handle_last_control_blur` (`dpd_fields_examples.py:315`) | blur | writes variants to the speech-marks store — disk I/O |
| `_click_edit_compound_types` / `_click_edit_phonetic_changes` (`:1576`, `:1599`) | click | subprocess to an external editor |

The three marked **change** are keystroke paths, budget 50 ms.

---

## Commit semantics

Read from all 48 field handler bodies in Phase 2b.

**No handler in the field system writes to the database.** The only one that
opens a session (`_search_and_fill_sanskrit`) reads. Field handlers validate
and set `error_text`, autofill other fields, clean their own value, write into
the `_add` shadow column, and move focus. The commit is the view's
`Add to DB` / `Test` button.

Consequence: a half-migrated field handler cannot write to dictionary data.
The residual risk is a handler overwriting another *form* field before save.
`_strip_var_phonetic_dupes` (`:1409`) does exactly that — rewriting `synonym`,
`synonym_add` and `var_text` as a side-effect of touching `var_phonetic` — by
design. Test it deliberately.

---

## Branch-in-place: cost and benefit

**Decided by the user:** branch in the main working tree, no worktree.

**Benefit.** `dpd.db` (2.26 GB, `.gitignore:1`) and `config.ini`
(`.gitignore:40`) are untracked and survive a branch switch. Confirmed in
Phase 1: both present after the switch, and row 1 (`a 1.1`, pos `letter`) reads
back. The app is runnable on either branch with no provisioning.

**Costs:**

1. **One environment, two incompatible pins.** One `.venv`, one Flet.
   `git switch` does not change it. Every switch between `main` and `flet-1-0`
   must be followed by `uv sync --all-groups`.

2. **Concurrent kamma threads share this tree.** Before any switch, snapshot
   `git status --porcelain` and check for unrecognised work. Never `git stash`,
   `git checkout -- <path>`, `git restore`, or `git reset --hard`.

   The tree sits on `flet-1-0` for the duration of battle-testing. Any other
   session that commits during that window commits onto `flet-1-0`, not `main`.
   This must be the first line of the handover document.

3. **The live database is in play.** Back it up before Phase 3. The commit-
   semantics finding above limits, but does not eliminate, the exposure —
   the pass views and tab views have not been catalogued yet.

`gui2/main.py:437` starts the FastAPI server at app startup against the same
database.

---

## The three risks

### 1. Threading model

In 0.28 each sync handler was dispatched to a thread pool. In 1.0 sync handlers
run directly on the event loop. All handlers here are synchronous; `gui2/` has
zero `async def`.

Any handler reaching the database, a subprocess, a sleep, or an AI service now
freezes the UI for its duration. No test catches this.

Approach: measure first, convert what is slow. Offload priority:
`asyncio.to_thread` when the result is needed; `page.run_thread` for
fire-and-forget; `page.loop.run_in_executor` for a bounded pool; generator
handlers that `yield` to flush updates mid-execution.

**Five handlers must become `async def` regardless of measured speed**, having
no sync alternative in 1.0: the two clipboard handlers (BR-5), the keyboard
scroll handler and its eg-dialog partner (BR-4), and the two updater file
picker handlers (BR-9).

### 2. Automatic updates

1.0 calls `page.update()` after every handler and after `main()` returns. The
372 manual calls become mostly harmless no-ops, except:

- mid-handler progress updates stop painting until the handler returns; fix by
  `yield`;
- `update()` raises on an unattached control and on a frozen one (BR-13), both
  silent no-ops in 0.28.

### 3. Web deployment divergence

Target is a **dynamic** webapp (server-side CPython), not static Pyodide. The
guide confirms a dynamic site runs Python as an ordinary CPython process, so
threads work as on desktop and `page.run_thread` / `asyncio.to_thread` remain
valid. If the target were static/Pyodide, threads vanish and every blocking
handler must become genuinely async.

---

## What it should do

### 1. Capture behaviour before touching anything

The user chose both capture methods and rejected driven-UI tests on the grounds
that the code is about to change underneath them.

**(a) Wiring inventory — done.** `artifacts/capture_wiring.py` emits file, line,
control class, and every `on_*` binding with its callable. 463 bindings, 96
files, in `artifacts/wiring_baseline.txt`.

It resolves three layers of indirection, because a grep for `ft.Dropdown` finds
none of the editor's dropdown fields: the `Dpd*` class hierarchy;
`FieldConfig(field_type=...)` via the `create_fields` dispatch, parsed from
source at scan time; and `super().__init__` inside a wrapper.

It captures both binding forms — call keyword and assignment. Scanning calls
alone missed `page.on_keyboard_event = ...`, which is BR-4's own site.

**(b) Behaviour catalogue — in progress.** `artifacts/behaviour_catalogue.md`.
Prose per handler, by screen, including ordering rules between focus, change,
blur and submit. Done: `dpd_fields.py` (all 48 fields) and
`dpd_fields_examples.py`. Remaining: 5 composite field modules, pass views, tab
views, popups.

**Named cost of rejecting driven-UI tests:** nothing mechanical protects the
behaviour half. The wiring diff catches a lost binding; only battle-testing
catches "fires, but now does the wrong thing."

### 2. Migrate

BR-17 and BR-14 first — nothing runs until BR-17 is done. Then pin, entry
points, renames, dialogs, dropdowns, clipboard. Then threading, informed by the
measurements.

### 3. Verify

Regenerate and diff the inventory; walk the catalogue in the running app; keep
`tests/gui2/` green; `just typecheck`, `ruff`, `pyright` clean.

### 4. Hand over

Branch stays unmerged; user battle-tests; switching over is a later decision.

---

## Assumptions & uncertainties

**Assumptions (flag if wrong):**

1. The webapp target is dynamic (server-side CPython), not static/Pyodide.
   Stated by the user, corroborated by the guide. If wrong, the threading
   strategy is wrong.
2. Declarative UI (`@ft.component`, hooks) and the new router are not adopted.
3. No async database driver. Blocking DB calls are offloaded to threads.
4. `flet[all]` provides everything used. Verified.
5. The agent creates and switches the branch only — not commits, not pushes,
   and never any whole-tree command. Explicit user override of the standing
   "never run git unprompted" rule.

**Uncertainties:**

- How much constructor-time rework each of the 23 BR-17 sites needs. Known to
  be per-view; the size is not known until each is read.
- How many further BR-13 `update()` sites exist outside the field system. One
  confirmed; the pass views and tab views are not yet catalogued.
- How many handlers the measurement phase flags as slow. The table above is a
  reading-based shortlist, not a measurement.
- Whether `on_select` alone preserves 0.28 behaviour for `root_key`, or whether
  it wants `on_text_change` too. User's call.

---

## Responsiveness target

The standard is "does it feel sluggish". Translated:

| Handler class | Feels instant | Acceptable | Must be fixed |
|---|---|---|---|
| Keystroke paths — `on_change`, `on_text_change`, typing in an editable dropdown | < 16 ms | < 50 ms | **> 50 ms** |
| Focus / blur / submit — moving between fields | < 50 ms | < 150 ms | **> 150 ms** |
| Button clicks with no visible progress indicator | < 100 ms | < 300 ms | **> 300 ms** |
| Deliberate long actions with a spinner or progress text | — | any duration | **any freeze of the window** |

A keystroke path runs on every character, so a 60 ms handler makes typing lag;
16 ms is one frame. Field-to-field movement happens constantly during editing
and is where sluggishness is felt first. A click is a discrete act with more
headroom, but past ~300 ms with nothing changing on screen it reads as a hang.

**The last row is the acceptance criterion.** Under 0.28 nothing froze the
window because every handler had its own thread. Under 1.0 a long handler
freezes everything. The binding rule: the window must never stop responding,
for any duration, on any action. The millisecond rows are diagnostic aids for
finding offenders during measurement.

---

## Structural improvement — the rule

**Decided by the user, 2026-09-17, replacing the revision 1–6 "no refactors"
constraint.** BR-17 and BR-14 mean much of this code is being rewritten, not
translated. Where a rewrite is happening anyway, take the opportunity to improve
the structure.

**The goal is not a copy of the old app. It is a structurally better app with
identical behaviour.**

That is a licence with a boundary, not a licence to refactor. The boundary:

### The unit of permission is the edit you already have to make

| Situation | Improvement allowed? |
|---|---|
| A function the migration rewrites (a BR-17 constructor, the BR-14 tab machinery) | **yes** — restructure it properly while it is open |
| A handler being offloaded in Phase 4 | **the offload boundary only** — see below |
| A function the migration edits in one line (a button rename, a constant) | **no** — change the one line |
| A file the migration does not touch | **no** |
| Something noticed in passing | **no** — log it as `NOTICED — NOT TOUCHING` |

**The Phase 4 clause is narrower than the others, deliberately.** BR-17 and
BR-14 each open a bounded, enumerable set of code — 23 constructors, one tab
machinery. "A handler being offloaded" is not bounded: Phase 4 will touch dozens,
and a general licence there would put every handler's internals in scope.

So in Phase 4 the permission covers **what runs where** — the offload boundary,
the per-call construction hoisted out of the handler, the session or manager
lifetime — and **not the handler's internal logic**, unless that specific
restructure was **pre-logged as a candidate in `artifacts/improvements.md`
before Phase 4 began**. C4, C5, C7 are pre-logged and stay in scope on that
basis.

No drive-by cleanups. No "while I'm here" in a neighbouring function. If the
migration did not force the file open, it stays shut.

### Three questions before any improvement

1. **Is the surrounding code being rewritten for a BR item anyway?** If no,
   stop.
2. **Can the behaviour be proved unchanged by the gates already in the plan** —
   the wiring inventory diff and the field's behaviour catalogue entry? If the
   answer needs a new kind of evidence, it is too big for this thread.
3. **Would a reviewer be able to tell, from the diff, which lines are the
   migration and which are the improvement?** If not, split them or drop the
   improvement.

### What identical behaviour means here, operationally

Two existing gates, no new ones:

- **`artifacts/wiring_baseline.txt` diff** — every handler still bound, to the
  same callable, on the same control class. An improvement that moves a binding
  must show up in `wiring_diff.md` with a reason.
- **`artifacts/behaviour_catalogue.md`** — the user-visible entry for that
  handler is unchanged, confirmed by walking it in the running app.

If an improvement cannot be checked against both, it does not go in.

### In scope

Structural changes that are invisible from outside:

- hoisting per-call construction out of a handler (a manager rebuilt on every
  blur becomes one instance)
- removing duplicated guard logic across several entry points into the same
  private method
- replacing an index-parallel data structure with a single keyed one, where the
  migration is already rewriting the indexing
- extracting a repeated inline lambda into a named method
- type hints on code being rewritten, per the project's modern-form convention
- deleting genuinely dead branches proven unreachable

### Out of scope

- Renaming anything for taste, including the 45 `ft.dropdown.Option` sites and
  the 22 safe `self.page` assignments.
- Moving code between files, splitting files, changing module boundaries.
- Changing any public shape another module imports.
- The synchronous database layer.
- Fixing existing bugs. They migrate as-is and get their own thread. The typo at
  `dpd_fields.py:1157` stays.
- Adopting declarative UI, components, hooks or the router.
- Anything in a file the migration does not otherwise open.

### Record-keeping

Every improvement is logged in `artifacts/improvements.md`: what changed, which
BR item opened the file, and what proves behaviour is identical. A reviewer
reads that file to separate migration from improvement.

**Improvement commits are separate from migration commits** (user's decision,
2026-09-17). Never mix a restructure into the same commit as a rename or an API
fix, and never into the same hunk. If a file needs both, do the migration edit,
commit it, then do the improvement.

This is what makes the rollback rule below usable: reverting an improvement has
to be a single revert, not an unpicking exercise. It also means a bisect during
battle-testing lands on one or the other, never on both at once.

The user commits; the agent does not run git. Sequence the work so the commits
fall out cleanly and say which is which when handing over.

### The rollback rule

If a review finding or a battle-testing bug is ambiguous — *is this the
migration or the refactor?* — revert the improvement, confirm the bug persists
or disappears, and re-apply only if it was innocent. Migration correctness wins
over structural gain, every time.

**The mechanism is the log, not the commit boundary.** Settled 2026-09-17.

"Revert the improvement" would ideally mean reverting one commit. But this
project's convention is that the **user commits everything at the end** and the
agent never runs git, so a phase-boundary commit scheme would ask the user to
change how they work for the agent's convenience. It does not.

So: **`artifacts/improvements.md` is the separation mechanism.** It maps every
improvement to the BR item that opened it and to specific call sites, which
makes rollback "revert these named hunks" rather than "revert that commit". The
Phase 7 audit already checks the log against the diff in both directions, so the
mapping is kept honest.

Two things follow, and they are requirements, not preferences:

- **Sequence migration edits before improvement edits, per file.** It costs
  nothing, and it means the improvement is always the later, smaller, separable
  hunk.
- **Never mix a restructure into the same hunk as a rename or an API fix.**
  A hunk that does both cannot be reverted independently, which defeats the
  mechanism entirely.

If the user does choose to commit at phase boundaries, migration first then
improvements, the rollback gets cheaper — but nothing here depends on it.

---

## Constraints

- Branch only. No merge to `main`. No commits without being asked.
- Concurrent threads share this working tree. Never `git stash`,
  `git checkout -- <path>`, `git restore`, or `git reset --hard`. Snapshot
  `git status --porcelain` before every branch switch.
- One `.venv`; every branch switch needs `uv sync --all-groups`, never bare
  `uv sync`.
- Back up the live database before Phase 3.
- **Behaviour preservation is absolute; structural preservation is not.** See
  the rule above. Identical observable behaviour, better structure where the
  migration is already rewriting the code.
- Touch a file, own its lint: `ruff check --fix`, `ruff format`, `pyright` per
  file; `just typecheck` repo-wide before finishing.
- Type hints everywhere, modern forms. `Path` not `os`. `icecream` not `print`.
- No `sys.path` hacks; scripts run from the project root.

---

## How we'll know it's done

1. `flet[all]==1.0.0` installs on Python 3.13 with no `error:` lines.
2. `artifacts/check_self_page.py` reports 0 breaks and all 22 safe sites intact.
3. The editor launches and all 16 tabs render, each building on first selection.
4. Regenerated wiring inventory diffs against the baseline with zero unexplained
   differences. A line moved by a structural improvement counts as explained
   only if `artifacts/improvements.md` names it.
5. Every catalogue entry walked in the running app and confirmed.
6. Every one of BR-1 to BR-17 has a specific confirmation recorded in the plan.
   For the silent failures (BR-1, BR-4, BR-14's Ctrl+S path, BR-16) that means
   watching the behaviour, not the absence of an error.
7. The window never stops responding on any action, and no handler exceeds its
   class threshold — confirmed by re-running the instrumentation with a stated
   sample count per handler.
8. `uv run pytest tests/gui2/` matches its result on `main`.
9. `just typecheck` clean; `ruff check` and `pyright` clean on every touched
   file.
10. The 7 data-integrity GUI helpers and the 4 updater files launch.
11. Every improvement taken is logged in `artifacts/improvements.md` with the BR
    item that opened the file and the evidence behaviour is unchanged. An
    improvement not in that log is a review finding.
12. The user has run the migrated editor for real editing work and reported back.

---

## What's not included

- Merging to `main` or switching the project over.
- Declarative UI, components, hooks, the new router.
- An async database layer.
- Driven-UI / on-device tests.
- Deploying the dynamic webapp.
- Flet packaging / `flet build`. The daily driver is `uv run python gui2/main.py`
  via `just gui`; `gui2/build/` is a gitignored leftover.
- Cosmetic renames that are not breaking (`ft.dropdown.Option`, the two
  `ft.border.BorderSide` calls, the 22 safe `self.page` assignments).
- Any behaviour change, bug fix, or feature. Existing bugs migrate as-is.
- Structural improvement outside the boundary in the rule above — that is,
  anywhere the migration does not already open the file.
- `archive/` and `kamma/archive/` Flet files.
