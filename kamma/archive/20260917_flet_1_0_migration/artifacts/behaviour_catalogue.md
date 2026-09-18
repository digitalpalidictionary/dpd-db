# Behaviour catalogue — what every handler does, from the user's side

Captured on **Flet 0.28.3**, branch `flet-1-0`, before any migration work.

**Why this exists.** The wiring inventory (`wiring_baseline.txt`) proves a
handler is still attached after the migration. It cannot show the handler still
does the right thing. Driven-UI tests were rejected because the code changes
underneath them, so this catalogue plus battle-testing is the only check on
logic drift.

**How to use it.** After Phase 3, walk each entry in the running app and tick it
in place. An entry that cannot be confirmed is a finding, not an oversight.

**How it was built.** Every entry was read out of the handler body, not inferred
from the handler's name. Where a name is misleading, that is called out.

Progress:

- [x] **1. Field system** — `dpd_fields.py` and the six composite field modules
      (164 bindings)
- [x] **2. Pass views** — pass1 add/auto, pass2 add/auto/pre, pass2x
      in-commentary (94 bindings)
- [x] **3. Tab views** — global, translations, compound-type, filter, tests,
      roots, sandhi, bold-search (106 bindings)
- [x] **4. Popups, shell and standalone windows** — app shell, shared popup,
      word finder, AI search, find-replace, test manager, username, utilities
      (51 bindings)

**Coverage: 415 of the 449 in-scope bindings, across 35 files. Zero
uncatalogued.** The four section totals reconcile exactly:
164 + 94 + 106 + 51 = 415, no bindings unaccounted.

The remaining 34 bindings are `db_tests/gui/`, catalogued in Phase 6 alongside
their migration.

Checked mechanically, not by eye:
`uv run kamma/threads/20260917_flet_1_0_migration/artifacts/check_catalogue_coverage.py`
exits non-zero while any in-scope file is unmentioned.

---

# 1. Field system

The main editor body. 48 declared fields; 164 of the repo's 463 handler
bindings. All the focus/change/blur/submit interplay is here.

## 1.1 How a field is wired — read this before the tables

Nothing here binds a handler to a control directly. There are three hops:

1. **`FieldConfig`** (`dpd_fields_classes.py:4`) — a plain declaration:
   a name, a `field_type`, and up to four handlers. The 48 configs are the
   list at `dpd_fields.py:92-306`. **This is the only place to read to know
   what is wired to what.**
2. **`create_fields()`** (`dpd_fields.py:313`) — dispatches on `field_type` to
   one of eight control classes, passing the handlers through.
3. **The `Dpd*` wrapper** — `DpdTextField`, `DpdDropdown` and the six composite
   field classes, each forwarding the handlers into a real Flet control.

Two consequences for the migration:

- A grep for `ft.Dropdown` finds none of the editor's dropdown fields. They are
  `FieldConfig(field_type="dropdown")` entries three hops away (BR-1).
- Every field also gets a shadow `_add` field (`dpd_fields.py:408`), a read-only
  `DpdText` holding a machine suggestion. Always created, mounted only in
  Pass2Add — see §1.6 (BR-13).

## 1.2 Commit semantics — when does a value reach the database?

**For every field in this system, the answer is the same: never, until the user
presses an explicit save button.** Read from the handler bodies, not assumed.

No handler in `dpd_fields.py` writes to the database. `_search_and_fill_sanskrit`
(`:997`) is the only one that opens a session at all, and it only *reads*. Field
handlers exclusively do one or more of:

| What a field handler actually does | Example |
|---|---|
| validate and set `error_text` | `pos_blur`, `pattern_change`, `family_word_change` |
| autofill another field | `pos_blur` → `grammar`, `trans_blur` → `plus_case` |
| autofill itself | `origin_blur` → `"pass2"`, `source_1_focus` → `"-"` |
| clean its own value | `clean_pali_field`, `sanskrit_blur` |
| write a suggestion into the `_add` shadow field | `construction_blur`, `phonetic_focus` |
| move focus | many |

The commit is `Add to DB` / `Test` in the view's bottom bar, outside this
system. A half-migrated field handler therefore cannot write to dictionary data.

A field handler can still overwrite another field's value **in the form**.
`_strip_var_phonetic_dupes` (`:1409`) rewrites `synonym`, `synonym_add` and
`var_text` as a side-effect of touching `var_phonetic` — by design, per the
exclusivity rule. A misfiring `var_phonetic` handler would silently discard
typing in two other fields. Test deliberately.

## 1.3 The BR-1 decision table — dropdowns

The nine sites whose handler must become `on_select` (and/or `on_text_change`).
**Default is `on_select` alone**, which reproduces 0.28 exactly.

Only **two** of the eight dropdown *fields* are affected; the spec's claim of
eight was wrong (corrected in `spec.md` BR-1).

| # | Site | Field | 0.28 handler does | Proposed 1.0 |
|---|---|---|---|---|
| 1 | `dpd_fields.py:153` | `root_key` | looks the root up and shows its gloss in `helper_text` | `on_select` |
| 2 | `dpd_fields.py:199` | `derivative` | generates `suffix` from `construction`, but **only if `suffix` is empty** | `on_select` |
| 3 | `dpd_fields_classes.py:62` | the `DpdDropdown` wrapper | forwards whatever it was given | `on_select` |
| 4 | `dpd_fields.py:326` | the fan-out feeding the wrapper | forwards `config.on_change` | `on_select` |
| 5 | `compound_type_tab_view.py:80` | CT tab, a filter dropdown | mirrors the value into `helper_text` | `on_select` |
| 6 | `compound_type_tab_view.py:96` | CT tab, a second dropdown | same | `on_select` |
| 7 | `dpd_fields_family_set.py:35` | family-set picker | see §1.5 | `on_select` |
| 8 | `filter_tab_view.py:392` | Filter tab preset picker | loads the chosen preset | `on_select` |
| 9 | `pass1_add_view.py:84` / `pass2_add_view.py:198` | history dropdowns | jumps to the chosen past word | `on_select` |

**Settled 2026-09-17: all nine sites take `on_select` alone.** `root_key` is
`editable=True` with filtering, and its handler shows the root's gloss — under
0.28 only on selection. `on_text_change` would update it while typing, which is
a behaviour change, so it is not taken. The thread's standing rule is to
preserve current behaviour.

Two further reasons it would have been the wrong call here: `root_key_change`
calls `db.get_root_string()`, so `on_text_change` puts a database read on the
keystroke path against the spec's 50 ms budget; and if live gloss is ever wanted
it should arrive in Phase 4 with offloading attached, not as a handler swap in
Phase 3.

## 1.4 Per-field catalogue

Read as: *user does X → sees Y*. `→` marks a write into another field.

### Identity and lemma

| Field | Event | What the user sees |
|---|---|---|
| `id` | submit (Enter) | field fills with the next free id, keeps focus |
| `lemma_1` | change, submit, blur | red "already in db" if the lemma exists **and** the word was not loaded from the db; "required field" if emptied on a loaded word |
| `lemma_1` | change/submit, new word | triggers the view's example and commentary search for the typed headword |
| `lemma_1` | **blur only** | if the lemma ends `sutta`/`vagga`: → `meaning_lit` gets `"discourse on "` / `"section on "`, and → `compound_type` gets `kammadhāraya`. Both only when the target is empty |
| `lemma_1` | submit (not blur) | keeps focus. On blur it lets focus go — deliberate, `:782` |
| `lemma_2` | blur | if `lemma_2_done` is not yet set, copies the cleaned `lemma_1` in |
| `lemma_2` | submit | recomputes from `lemma_1` + `pos` + `grammar` |

### Grammar block

| Field | Event | What the user sees |
|---|---|---|
| `pos` | blur | unknown value → up to 3 fuzzy suggestions in red, focus stays; **then** fills `lemma_2` (once only, sets the done flag); **then** if `grammar` is empty, seeds it `"<pos> of "` for verbs/participles or `"<pos>, "` otherwise, and jumps focus there |
| `grammar` | blur | if it contains `" of "` or `" from "`, extracts what follows → `derived_from`, strips a leading `na `, drops everything after a comma. Once only |
| `trans` | blur | value `trans` → `plus_case` becomes `+acc` and takes focus |
| `neg`, `verb`, `plus_case` | — | dropdowns, no handlers at all |
| `derived_from`, `non_root_in_comps` | — | no handlers |

### Meanings

| Field | Event | What the user sees |
|---|---|---|
| `meaning_1` | focus | if empty and the lemma ends `sutta`/`vagga`, copies `meaning_2` in |
| `meaning_1` | blur | **recomputes synonym suggestions** — clears the done flag and runs the detector, writing into `synonym` and `synonym_add` (§1.5) |
| `meaning_lit`, `meaning_2` | — | no handlers |

### Root block

| Field | Event | What the user sees |
|---|---|---|
| `root_key` | focus, change, blur | known root → its gloss appears as grey helper text. Unknown → helper and error both cleared. **Never shows an error for an unknown root** — read the body, `:1090`, this looks like a validation and is not one |
| `root_sign` | focus, change, blur | "no root_key" if a sign is set without a key; "no root_sign" if a key is set without a sign |
| `root_sign` | submit | fills with the next sign for the current `root_key`, keeps focus |
| `root_base` | submit | fills with the next base for the current key+sign, keeps focus |
| `family_root` | submit | fills with the next root family for the key + current construction, keeps focus |
| `family_root` | blur | red if the cleaned root key is not a substring of the value ("don't match" — note the typo in the message, `:1157`); red "unknown root family" if not in the known set |

### Families

| Field | Event | What the user sees |
|---|---|---|
| `family_word` | focus, change | red if `root_key` is also set ("Cannot have both"); red if it contains a space; otherwise unknown → up to 3 fuzzy suggestions. **Every one of these also steals focus back to the field** |
| `family_compound` | focus | if empty and not yet done: copies the cleaned lemma in and takes focus — **unless** the lemma ends `sutta`/`vagga` or `pos` is `sandhi`/`idiom`. The done flag is set either way |
| `family_compound` | change, blur | each space-separated part checked against known compound families; unknown ones listed in red |
| `family_idioms` | focus | if empty and `family_compound` has no space, copies it in. **Always** re-focuses itself |
| `family_set` | — | see §1.5 |

### Construction and derivation

| Field | Event | What the user sees |
|---|---|---|
| `construction` | focus, empty | builds a construction from lemma + grammar + root parts + `neg`, takes focus, marks done |
| `construction` | focus, non-empty | validates every `+`-separated part of **line 1 only** against known lemmas; unknown ones listed in red |
| `construction` | change | pressing Enter on a non-empty field appends the cleaned lemma on the new line, and **clears** the done flag |
| `construction` | blur | **skipped entirely if `root_key` is set.** Otherwise runs compound-type detection and writes the result into `compound_type_add` — the red suggestion column, never the field itself |
| `derivative` | change | if `suffix` is empty, `pos` is a declension and `grammar` has no `comp`: derives the suffix from the construction's last `+` part, fills it, takes focus |
| `suffix` | change | typing anything clears a previous error |
| `compound_type` | blur | moves focus into the compound-construction sub-field |
| `compound_construction` | — | composite field, see §1.5 |

### Phonetic, Sanskrit, variants

| Field | Event | What the user sees |
|---|---|---|
| `phonetic` | focus | runs the phonetic-change rules over the current headword; suggestions go into the field if empty, otherwise into `phonetic_add` |
| `sanskrit` | focus | if not done and empty, **searches the database** and fills (§1.6 — this is slow) |
| `sanskrit` | blur | first normalises known `sūkta, sūtra (bsk)` mess patterns and the `vyagra + varga` prefix; then the same search if still empty |
| `sanskrit` | submit | forces a fresh search regardless of the done flag |
| `non_ia` | blur | triggers the same Sanskrit search if `sanskrit` is still empty — a fourth entry point to the same slow call |
| `synonym` | focus | computes synonyms if not already done — the fallback for tabbing straight past `meaning_1` |
| `synonym` | submit | forces a fresh recompute |
| `synonym` | change, blur | strips anything outside the Pāḷi alphabet, comma and space |
| `var_phonetic` | focus | computes phonetic variants if not done; fills field + `_add`, and puts the matched rule per lemma into helper text |
| `var_phonetic` | submit | forces a fresh recompute |
| `var_phonetic` | blur | cleans to Pāḷi characters, **then removes any lemma it now shares with `synonym` or `var_text` from those two fields** |
| `var_text`, `antonym` | change, blur | Pāḷi-character cleaning only |

### Sources, examples, notes, admin

| Field | Event | What the user sees |
|---|---|---|
| `source_1` | focus | if empty and the lemma ends `sutta`/`vagga`, fills `-` |
| `commentary` | focus | same `-` autofill; the composite field is §1.5 |
| `notes` | blur | spell-checks the whole value; misspellings shown as `word: suggestion, suggestion` in red |
| `origin` | blur | if empty, fills `pass2` |
| `stem` | submit | recomputes `stem` **and** `pattern` from pos + grammar + lemma, keeps focus |
| `stem` | blur | the same, but once only (done flag) |
| `pattern` | focus, change | unknown pattern → up to 3 fuzzy suggestions in red **and focus is stolen back**. Loads the pattern set on first use |
| `comment` | focus, change, blur | **only when the logged-in user is not the primary editor**: red "Add a comment" while empty |
| `sutta_1`, `sutta_2`, `source_2`, `translation_1/2`, `cognate`, `link` | — | no handlers |

### The transfer buttons

Every field row in Pass2Add carries a `←` button between the `_add` suggestion
and the real field. Disabled when the suggestion is empty. Clicking copies the
suggestion across — except for `synonym` / `var_phonetic` / `var_text`, where it
applies the exclusivity rule instead, so accepting a lemma into one **removes it
from the other two** (`transfer_add_value`, `:629`).

`check_and_color_add_fields` (`:590`) colours a suggestion **red when it differs
from the real field** and grey when it matches. That is the visual cue the
editor works from all day; it must look identical after the migration.

## 1.5 Composite field types

Six field types are whole `ft.Column` subclasses, not text boxes.

- [x] `dpd_fields_examples.py` — 20 bindings
- [x] `dpd_fields_commentary.py` — 14 bindings
- [x] `dpd_fields_meaning.py` — 7
- [x] `dpd_fields_notes.py` — 6
- [x] `dpd_fields_compound_construction.py` — 5
- [x] `dpd_fields_family_set.py` — 5

All six share a shape worth knowing before reading the entries:

- The outer class is an `ft.Column`; the editable control is an inner
  `DpdTextField`. `value`, `field` and `error_text` are properties forwarding to
  it, so `dpd_fields.get_field("notes").value` reads the inner field.
- **The `error_text` setter calls `.update()` on the inner field** in all six.
  `clear_messages()` (`dpd_fields.py:583`) sets `error_text = None` on every
  field, so it fires all six. Phase 5 must confirm `clear_messages` is never
  called before the view is mounted (BR-13).
- Only `DpdMeaningField` also defines `color` and `helper_text` properties. On
  the other five those assignments land on the `Column` and do nothing. Harmless
  today; do not "fix" it.
- All six assign `self.page` in `__init__` (BR-17).

### `example_1` / `example_2` — the example field

Two modes. In **simple mode** it is just the text box. Otherwise it carries a
hidden tool panel, revealed by the eye icon at the top of the field.

| Control | Event | What the user sees |
|---|---|---|
| eye icon | click | shows/hides the search row and the button row together; when showing, focus jumps into the book dropdown and the icon flips to the "open eye" |
| `book` dropdown | blur | focus moves straight on to "word to find" |
| `word to find` | submit | **searches the CST book for the word** (§1.6 — slow), then either opens the chooser dialog or shows red "no example found" in the field. Focus returns to the field either way |
| chooser dialog | radio select | records which example is selected; nothing visible changes |
| chooser dialog | OK | closes, and writes the chosen source, sutta and cleaned example into `source_N`, `sutta_N`, `example_N` |
| chooser dialog | Cancel | closes, changes nothing |
| `Add '-` | click | re-runs example cleaning over the current text |
| `[]` | click | strips square brackets |
| `<b>` | click | strips bold tags |
| `Delete` | click | clears source, sutta and example for **this** example slot |
| `Swap` | click | exchanges **all** of source/sutta/example between slots 1 and 2 |
| `Stash` | click | saves the current source/sutta/example to the shared stash; message "Stashed current example data" |
| `Reload` | click | restores from the stash, or message "No stashed data found" |
| `Last` | click | restores the last example captured on blur (see below); silent if there is none |
| `bold` box | submit | wraps every occurrence of the typed word in `<b>…</b>` in the example, keeps focus in the bold box |
| `bold` box | **blur** | three things at once: hides the tool panel if open; **saves the current example as "last"**; and if the example contains `'` or `-`, feeds every such word into the speech-marks manager as a variant |
| example text | focus | refreshes the character counter |
| example text | change | replaces the typing shortcuts `THA`/`THI` with their full formulae, normalises `...` and ` ...` to `…`, fixes `'nti` → `n'ti`, then refreshes the counter |

**The counter.** Over 300 characters (excluding bold tags), the example's border
and text both turn red and the error text shows the overage. Under 300, all
three are cleared. Updates per keystroke.

The red border is a BR-16 site — 1.0 resolves border colours from the theme
unless an explicit `side` is given. Check an over-length example still goes
visibly red and a normal one returns to its usual border.

### `commentary` — the commentary field

Same eye-icon tool panel as the example field, with a search over bold
definitions instead of CST books.

| Control | Event | What the user sees |
|---|---|---|
| eye icon | click | shows/hides the search row; when showing, focus jumps to search field 1; when hiding, focus returns to the commentary text |
| search field 1 | focus | if empty and the search has not run yet, fills with the cleaned lemma **minus its last character**, and marks the search done |
| Search | click | same autofill first if still empty, then searches bold definitions. Results → the chooser dialog. No results → red "not found" in search field 1, **and** if the commentary is empty it is set to `-` and takes focus; otherwise focus returns to search field 1 |
| chooser dialog | checkboxes | multi-select — unlike the example chooser, which is single-select radios |
| chooser dialog | OK | joins every checked result as `(ref_code) commentary` on its own line, cleans the lot, and writes it into the commentary field, which takes focus |
| chooser dialog | Cancel | closes and **sets the commentary to `-`**, then focuses it. Not a no-op — the example chooser's Cancel changes nothing, this one does |
| Clear | click | empties the commentary field |
| `Last` | click | restores the last commentary saved on blur; silent if none |
| commentary text | change | normalises ` ...`, `...` and ` …` to `…` |
| commentary text | blur | saves the current value as "last", then runs the field's external blur handler |
| last control | blur | hides the tool panel if open, then feeds every hyphen/apostrophe word into the speech-marks manager |

Note the result cap: the search asks for `MAX_SEARCH_RESULTS + 1` and shows an
amber "showing first N — refine your search" line when it got more.

### `meaning_1` / `meaning_lit` / `meaning_2` — the meaning field

Adds live spell-checking under the text box.

| Control | Event | What the user sees |
|---|---|---|
| meaning text | focus | runs the external focus handler first, **then** spell-checks — unless the previous action was adding a word to the dictionary, in which case the check is skipped exactly once |
| meaning text | blur | spell-checks, **then** runs the external blur handler. Note the order is the reverse of focus |
| spell suggestions | — | a red, selectable line below the field reading `word: sug1, sug2. word2: sug3`. Hidden when there is nothing to report |
| `Add spelling` | submit | adds the typed word to the custom dictionary, clears the box, **removes just that word from the suggestion line without re-running the check**, shows the dictionary's message, and returns focus to the meaning text |

The ordering matters: `meaning_1`'s external blur handler is
`meaning_1_blur`, which recomputes synonyms. So blurring `meaning_1` spell-checks
first, then runs the synonym detector.

### `notes` — the notes field

| Control | Event | What the user sees |
|---|---|---|
| notes text | focus / change / submit / blur | passed straight through to the field config's handlers; `notes` binds only `on_blur` → the generic spell check |
| `Italic` | submit | wraps the **first** occurrence of the typed text in `<i>…</i>`, clears the box, returns focus to the notes text. Silent if the text is not present |
| `Bold` | submit | the same with `<b>…</b>` |

### `compound_construction` — the compound-construction field

| Control | Event | What the user sees |
|---|---|---|
| construction text | focus | if `compound_type` has a value and this field is empty, generates the compound construction from the current headword. **Always** re-focuses itself afterwards |
| `Bold` | submit | wraps the typed text in `<b>…</b>`, preferring an occurrence followed by ` + `, falling back to the first occurrence anywhere. Clears the box and focuses the construction text. Silent if not present |

This field is where `compound_type`'s blur sends focus.

### `family_set` — the family-set field

| Control | Event | What the user sees |
|---|---|---|
| `Add Set` dropdown | change | appends the chosen set to the text field if not already there, re-sorts the whole list in Pāḷi order, joins with `; `, **clears the dropdown**, and puts focus back on the text field |
| set text | blur | splits on `;` and checks each part against the known sets. Unknown parts → up to 3 fuzzy suggestions each, concatenated, in red; or "Unknown set(s)" if nothing close |
| set text | focus / change / submit | passed through to the field config, which binds none of them |

The dropdown clearing itself after each pick is what makes it an "add" control
rather than a selector. Confirm that still happens under `on_select` (BR-1).

## 1.6 Migration hazards found while cataloguing

Found by reading behaviour, not by the breaking-change sweep.

### BR-13 — unattached `update()`, Pass1Add + `construction` blur

`construction_blur` (`:1564-1571`) ends with
`compound_type_add_field.update()`.

Pass1Add mounts the field system with `include_add_fields` at its default
`False` (`pass1_add_view.py:338` vs `pass2_add_view.py:715`). Every `_add` field
is created (`:408`) but added to no page. Under 0.28 `update()` on an unattached
control was a silent no-op; under 1.0 it raises
`RuntimeError: ... Control must be added to the page first`.

`construction` is in `PASS1_FIELDS`, so it is visible and editable in Pass1Add.
Blurring it after typing is a daily action, so this raises on the first Pass1Add
word after the upgrade.

Fix at the call site — guard on the add field being mounted, not by removing the
update, which is correct in Pass2Add.

`phonetic_focus` (`:929`) has the same shape, but `phonetic` is not in
`PASS1_FIELDS` and cannot be focused there.

### BR-17 — `self.page = page` in all six composite field classes

`DpdExampleField`, `DpdCommentaryField`, `DpdMeaningField`, `DpdNotesField`,
`DpdCompoundConstructionField` and `DpdFamilySetField` all subclass `ft.Column`
and assign `self.page` in their constructor. In 1.0 that is a read-only property
and the assignment raises at construction. Full 23-site list in `spec.md` BR-17.

### Blocking work on keystroke and focus paths (Phase 4 input)

Found by reading; to be confirmed by the Phase 2c measurement, not assumed:

| Handler | Event class | What blocks |
|---|---|---|
| `_search_and_fill_sanskrit` (`:997`) | focus / blur / submit | opens its own db session; `lemma_1 LIKE '%part%'` per construction part — unanchored scan of a 2.26 GB database, once per part. Four entry points |
| `family_word_change` (`:1196`) | change — per keystroke | fuzzy-match against every known word family |
| `pattern_change` (`:1657`) | change — per keystroke | fuzzy-match against every pattern; loads the pattern set on first use |
| `root_key_change` (`:1090`) | change — per keystroke | `db.get_root_string()` |
| `construction_blur` (`:1553`) | blur | constructs a `CompoundTypeManager`; re-reads its TSV every blur |
| `phonetic_focus` (`:913`) | focus | constructs a `PhoneticChangeManager`; re-reads its TSV every focus |
| `_compute_and_write_synonyms` (`:1314`) | `meaning_1` blur | relationship detector |
| `_compute_and_write_phonetic_variants` (`:1370`) | focus | phonetic-variant detector |
| `_click_edit_compound_types` / `_click_edit_phonetic_changes` (`:1576`, `:1599`) | click | subprocess to an external editor |
| `click_book_and_word` (`examples:344`) | submit | parses a CST book |
| `_handle_last_control_blur` (`examples:315`) | blur | writes variants to the speech-marks store — disk I/O |
| `_handle_last_control_blur` (`commentary:158`) | blur | the same speech-marks write |
| `click_commentary_search` (`commentary:203`) | click | constructs a `BoldDefinitionsSearchManager` per click, then searches |
| `_handle_blur` (`family_set:83`) | blur | fuzzy-matches each `;`-separated part against every known family set |
| `_handle_spell_check` (`meaning:161`) | focus **and** blur | spell-checks the whole value on both events |

Under 0.28 each ran on its own pool thread. Under 1.0 they run on the event
loop. The three per-keystroke handlers have a 50 ms budget.

### Not a hazard — hidden fields stay attached

`filter_fields` (`:493`) and `add_to_ui` (`:422`) hide a field by setting
`field_row.visible = False`. The control stays mounted, so `update()` on a
hidden field is safe in 1.0. Only the unmounted `_add` fields are affected —
Phase 5 does not need to audit all 48 fields.

### NOTICED — NOT TOUCHING

- `dpd_fields.py:931,934,1565` and `pass1_add_view.py:308` use `print()` for
  debug output; project convention is `icecream`. Out of scope — migration, not
  cleanup.
- `dpd_fields.py:1157` has a typo in a user-visible error message
  ("dont's match"). Out of scope.

---

# 2. Pass views

94 bindings across six views. These own the word queue, the commit to the
database, and the per-book automation.

**All six are `ft.Column` subclasses that assign `self.page` — BR-17.**

## 2.1 Where the database is actually written

The field system writes nothing (§1.2). These buttons do:

| View | Control | Effect |
|---|---|---|
| Pass2Add | `Add to DB` (`:226`) | `_click_add_to_db` — the main commit. Refuses with "Database still loading — please wait before saving" if the db is not ready. Defaults `origin` to `pass2` |
| Pass2Add | `Delete` (`:281`) | `_click_delete_from_db` — opens a modal confirm; the OK button is the destructive one |
| Pass1Add | `Add to DB` (`:157`) | `controller.make_dpd_headword_and_add_to_db()` |
| Pass1Add | `Delete` (`:182`) | removes the word from the queue JSON and advances — **does not delete from the database**, despite the label |
| Pass1Add | `Refresh DB` (`:121`) | new session + marks the corpus stale |

Everything else in these views edits the form, the queue file, or an external
store.

## 2.2 Pass2Add — 37 bindings

The main editing screen.

### Top bar — the queue loaders

Seven buttons, each pulling the next item from a different queue. All seven
share `on_hover=self._update_count_tooltip`.

| Button | Click | Hover |
|---|---|---|
| `P2A` (`:107`) | loads the next pass2-auto entry | tooltip shows that queue's remaining count |
| `New` (`:113`) | loads the next new word | count |
| `Cor` (`:119`) | loads the next correction | count |
| `Add` (`:125`) | loads the next addition | count |
| `X` (`:131`) | loads the next X-import entry — with an id it edits that headword and puts the queued values in the `_add` column; without one it fills the fields as a new word | count |
| `Eg` (`:137`) | loads the next eg-queue word: edit mode if it exists in the db, otherwise a prefilled new word | count |
| `PRead` (`:143`) | loads the next proofreader correction | tooltip shows the field name and remaining count |

Each loader reports "No more X words" and stops when its queue is empty.

⚠️ `_update_count_tooltip` (`:324`) **queries the queues on hover** and calls
`e.control.update()`. Hover fires constantly. It early-returns when
`e.data != "true"` (i.e. on hover-out), so it runs once per hover-in, not
continuously — but it is still a queue read on a mouse movement. Phase 2c should
measure it; the budget for a hover is the click row's 300 ms at most.

### Identity row

| Control | Event | What the user sees |
|---|---|---|
| `Enter ID or Lemma` (`:149`) | submit | loads that headword for editing |
| same | blur | disables the field's autofocus behaviour |
| `Clone` (`:163`) | click | copies a headword's values into the empty fields of the current form |
| `Split` (`:166`) | click | copies the current fields to a **new id**, increments `lemma_1`, and clears the fields that must not be shared. Refuses on an empty `lemma_1` |
| `Clear All` (`:169`) | click | empties the form |
| `⋮` menu → `Update Sandhi` (`:184`) | click | runs the sandhi update |
| `⋮` menu → `Update with AI` (`:188`) | click | requests an AI update for the loaded headword; refuses if no headword is loaded |
| `History` dropdown (`:198`) | change | loads the selected past headword back into the fields, message "loaded X from history" |

### Filter radios (`:210`)

`All` / `Root` / `Compound` / `Sutta` / `Word` / `Pass1` — switches which field
rows are visible via `filter_fields`. **A field with a value stays visible even
when the filter would hide it** (`dpd_fields.py:501-508`); that is deliberate
and must survive.

### Bottom bar

| Button | What the user sees |
|---|---|
| `Test` (`:275`) | clears messages, builds the current headword and runs the tests against it. Does nothing if `lemma_1` is empty |
| `Add to DB` (`:226`) | the commit — see §2.1 |
| `Delete` (`:281`) | opens the confirm dialog. Its `on_hover` (`_on_delete_hover`, `:319`) turns the button **red with white text** while the pointer is over it, and back on leaving — a deliberate "this one is destructive" cue |
| `Stash` (`:291`) | writes all current field values to the headword stash JSON. "Nothing to stash" if `lemma_1` is empty |
| `Unstash` (`:296`) | reads them back. "No stash found" if the file is absent |

The delete confirm dialog's OK (`:1000`) performs the deletion; Cancel (`:1001`)
closes it.

### The eg dialog (`:1326-1397`)

Opened by the `Eg` button's queue when it needs input.

| Control | Event | What the user sees |
|---|---|---|
| word field (`:1326`) | submit | adds the queued words |
| `Add` (`:1354`) | click | same |
| `Close` (`:1355`) | click | closes |
| dialog (`:1337`) | dismiss | `_restore_eg_kb` — puts the global keyboard handler back |

While this dialog is open the page's keyboard handler is **swapped**
(`:1367-1368`) so Enter means "add", with everything else forwarded to the saved
global handler. This is BR-4's second site — see §2.5.

## 2.3 Pass1Add — 17 bindings

| Control | What the user sees |
|---|---|
| `History` dropdown (`:84`) | loads the selected past headword into the fields |
| clone field (`:95`) / `Clone` (`:103`) | submit or click clones from an id or lemma; "Enter an ID or Lemma to clone from." if empty, "Headword 'X' not found for cloning." if unknown |
| `Process Book` (`:116`) | runs the book through the pass1 automation. Long-running |
| `Refresh DB` (`:121`) | new session, marks the corpus stale, message "Database refreshed" |
| `Clear` (`:126`) | **rebuilds the whole middle section** rather than blanking values, then clears `word_in_text` |
| `Add to DB` (`:157`) | the commit |
| `Test` (`:164`) | same shape as Pass2Add's |
| `Pass` (`:177`) | clears the form and advances the queue **without** removing the current item from the JSON |
| `Delete` (`:182`) | removes the word from the queue JSON and advances. "No word_in_text." if nothing is loaded |
| `Sandhi OK` (`:191`) | adds the current word to the sandhi checked list |
| `Add to Sandhi` (`:196`) | opens a popup asking for the construction, then records it |
| `Add to Variants` (`:201`) | popup, then records a variant |
| `Add to Spelling` (`:206`) | popup, then records a spelling mistake |

The three popups (`:258`, `:277`, `:290`) each return through their own
`on_submit` handler.

⚠️ **This is the view with the confirmed BR-13 crash** — blurring `construction`
here raises, because Pass1Add never mounts the `_add` fields (§1.6).

## 2.4 `pass2_pre_view.py` and `pass2x/in_commentary_view.py` — 13 bindings each

These two are near-identical in shape: a search bar, an exception field, a
book/run button, a four-button verdict row, and a paged example chooser.

| Control | Pass2Pre | Pass2x |
|---|---|---|
| search bar | `:83` | `:45` |
| word-in-text field | — | `:60` submit |
| exception field, submit | `:123` | `:94` |
| toggles | `:132` exceptions, `:137` in-comps | — |
| run button | `:154` `handle_book_click` | `:122` `handle_in_commentary_click` |
| `Yes` | `:185` | `:139` |
| `No` | `:189` | `:140` |
| `New` | `:193` | `:141` |
| `Pass` | `:197` | `:142` |
| `More` / `Less` | `:495` / `:501` | `:313` / `:319` |
| example radios | `:504` | `:323` |
| popup OK | `:337` submit, `:360` click | `:424` submit, `:447` click |

The four verdict buttons are the working loop: `Yes` accepts the suggestion and
advances, `No` rejects and advances, `New` starts a new entry, `Pass` skips
without recording. `More` / `Less` page the example list.

**Pass2x's "in commentary" rule:** an entry counts as incomplete when it lacks
`meaning_1` **or** `source_1` — it is *not* keyed on a missing sutta example.
Recorded because the two are easy to confuse.

## 2.5 `pass1_auto_view.py` and `pass2_auto_view.py` — 8 and 6 bindings

Batch automation over a whole book.

| Control | Pass1Auto | Pass2Auto | What the user sees |
|---|---|---|---|
| GoldenDict toggle | `:73` | `:84` | turns GoldenDict lookup on/off for the run |
| `No AI` | — | `:89` | runs the batch without the AI step |
| reload models | `:131` | `:101` | re-reads the AI model list |
| `Book` | `:126` | `:106` | starts the batch. **Long-running, with progress** |
| `Stop` | `:140` | `:110` | halts the batch |
| `Clear` | `:144` | `:114` | clears the output |
| `Text` submit / cancel | `:114` / `:113` | — | runs the batch over pasted text instead of a book |

These are the clearest "deliberate long action" handlers in the app: they must
keep the window responsive and the progress indicator moving, per the spec's
last responsiveness row.

## 2.6 Migration notes for this section

- **BR-17:** all six views assign `self.page`.
- **BR-4 second site:** `pass2_add_view.py:1360-1368,1395-1397` swap the page
  keyboard handler while the eg dialog is open and call the saved handler
  directly. Both handlers must convert together.
- **BR-5:** the two clipboard handlers (`:934`, `:1180`) live in Pass2Add.
- **BR-8:** the delete confirm dialog (`:975`) and the eg dialog (`:1337`), plus
  the legacy overlay-append pattern at `pass1_auto_view.py:193-197`.
- **BR-13 confirmed:** Pass1Add + `construction` blur.
- **BR-7:** these six views hold a large share of the 136 `ElevatedButton`
  sites.
- **Phase 4:** `_update_count_tooltip` reads queue state on hover; the batch
  runners and `Process Book` are the long actions; `_click_update_with_ai` is an
  AI round trip on a click.

---

# 3. Tab views

106 bindings across nine modules. All are `ft.Column` subclasses assigning
`self.page` (BR-17), except `filter_component.py`, which holds three control
subclasses of its own.

## 3.1 Global tab — `global_tab_view.py`, 4 bindings

Four buttons, **all four long-running, and all four emit progress messages
mid-handler**. This is the clearest instance in the app of the automatic-update
problem: in 1.0 nothing painted inside a handler reaches the screen until the
handler returns, so every one of these will show the user nothing at all and
then jump straight to its final message.

| Button | What the user sees today |
|---|---|
| `Backup & Quit` (`:32`) | "Running database backup…" → runs the TSV backup → "Database backup completed successfully." → **closes the app window**. On failure: "Backup failed: …" and the window stays open |
| `Open Internal Tests` (`:42`) | opens `db_tests_columns.tsv` in LibreOffice Calc. Silent if the file is missing — no message either way |
| `Update Anki` (`:52`) | "Closing Anki…" → `pkill -9 -f anki` → **sleeps 3 s** → checks with `pgrep`; if Anki is still there, "Warning: Anki may still be running, but proceeding anyway…" and **sleeps 2 s more** → "Updating Anki database…" → runs the Anki updater inline → "…completed successfully! Restarting Anki…" → relaunches Anki → "Anki has been restarted successfully!" |
| `Update Inflections` (`:62`) | "Updating inflections…" → runs the inflections manager → marks the corpus stale → rebuilds the inflection lists → "Inflections updated successfully." |

`Update Anki` is the worst case: two hard sleeps plus a full updater run, with
six progress messages that will all appear at once at the end. Phase 4 must
convert it, and Phase 5 must make the progress messages `yield`.

## 3.2 Translations tab — `translations_view.py`, 4 bindings

| Control | Event | What the user sees |
|---|---|---|
| search field (`:37`) | submit | runs the search |
| `Search` (`:63`) | click | same |
| `Clear` (`:66`) | click | empties the results |
| text-search field (`:70`) | submit | filters within the results |

This view holds the single `page.snack_bar =` assignment (`:127`) — BR-8's
fourth pattern, and the only one of its kind in the repo.

## 3.3 Compound Type tab — `compound_type_tab_view.py`, 27 bindings

The largest tab. Two modes: working through detection rules, and editing the
rules TSV.

| Control | Event | What the user sees |
|---|---|---|
| `Filter` (`:47`) | click | toggles the meaning filter |
| word field (`:67`) | submit | looks the word up |
| two dropdowns (`:80`, `:96`) | change | mirror the selected value into the control's own `helper_text`, blanking to a space when empty. **BR-1 sites** — inline lambdas calling `e.control.update()` |
| `+` (`:134`) | click | adds the typed type as a chip |
| type chips (`:286`) | delete | removes that type from the selection |
| `Add` (`:198`) | click | adds a new rule |
| `Update` (`:199`) | click | updates the current rule. Starts hidden |
| `→` (`:202`) | click | next rule. Starts hidden |
| `All` / `Correct` / `Wrong` / `Exceptions` (`:210-213`) | click | filter the result list by verdict |
| `Clear` (`:215`) | click | clears the form |
| `Delete` (`:216`) | click | deletes the rule; its `on_hover` turns the button red, same cue as Pass2Add's delete |
| `TSV` (`:221`) | click | opens the rules TSV externally |
| `←` / `→ TSV` (`:222`, `:223`) | click | step through TSV rules |
| `Save Changes` (`:253`) | click | writes the edited grid back |
| grid cells (`:904`) | change | tracked per row and column for the save |
| type cell (`:921`) | submit | autofills the compound type |
| construction cell (`:929`) | submit | autofills the compound construction from the lemma |
| exception field (`:987`) | submit | adds an exception |
| exception `+` (`:997`) | click | same, per row |
| confirm dialog (`:812`, `:813`) | click | confirm / cancel the delete |

The three `make_*` factories (`:904`, `:921`, `:929`) build per-cell handlers, so
the grid's wiring is generated rather than declared. The inventory records the
factory call, not one row per cell — expect that in the Phase 7 diff.

## 3.4 Filter tab — `filter_tab_view.py` 21 bindings, `filter_component.py` 6

A query builder over the headword table, with saved presets.

| Control | Event | What the user sees |
|---|---|---|
| `Apply Filters` (`:160`) | click | runs the query and fills the results table |
| any filter value field (`:219`, `:259`, `:377`) | submit | applies the filters — Enter anywhere in the builder runs it |
| `Clear Filters` (`:163`) | click | empties the builder |
| `Reset to Default` (`:166`) | click | restores the default filter set |
| `+` (`:251`) | click | adds a filter row |
| row `−` (`:232`, `:272`) | click | removes that row |
| `Select Columns` (`:328`) | click | shows/hides the column checkboxes |
| column checkbox (`:316`) | change | adds or removes that column from the results |
| preset dropdown (`:392`) | change | **BR-1 site** — loads the chosen preset |
| `Save` / `Rename` / `Delete` preset (`:403`, `:410`, `:418`) | click | each opens its own dialog (`:621`, `:664`, `:719` and partners) |

The results table (`filter_component.py`) is editable in place:

| Control | Event | What the user sees |
|---|---|---|
| `◀` / `▶` (`:138`, `:144`) | click | page through results |
| `Save Changes` (`:169`) | click | writes edited cells back to the database |
| a result cell (`:373`) | tap | turns that cell into a text field for editing |
| that text field (`:411`) | change | records the edit as pending |
| the cell (`:417`) | — | `on_tap = None` while it is being edited, restored after |

⚠️ `filter_component.py:487-495` flips a field's border to **red** on invalid
input and to transparent otherwise — a BR-16 site.

This view also holds the two `ft.border.BorderSide` calls (`:33,34`) that
**survive** 1.0 unchanged, next to the one `ft.border.all` call (`:32`) that does
not. Do not touch the first two.

## 3.5 Tests tab — `tests_tab_view.py`, 15 bindings

Every handler is on the controller, not the view.

| Control | What the user sees |
|---|---|
| `Run Tests` (`:65`) | runs the test suite. **Long-running with progress** |
| direction toggle (`:72`) | flips the iteration direction |
| `Stop` (`:77`) | halts the run |
| `Edit Tests` (`:84`) | opens the tests file externally (subprocess) |
| `Sort Tests` (`:91`) | re-sorts the test file |
| `Update` (`:98`) | saves the edited test definition |
| `Add New` (`:104`) | creates a test |
| `Delete` (`:110`) | deletes the current test |
| `Add Exception` (`:234`) | adds the current result as an exception |
| `Add All Exceptions` (`:238`) | adds every result in the list |
| `Rerun` (`:252`, `:264`) | re-runs the current test |
| `Next` (`:258`, `:270`) | moves to the next failing test |
| copy icon (`:293`) | copies the generated database query to the clipboard |

Two things to record:

- **The copy button uses `pyperclip`, not Flet** (`tests_tab_controller.py:698`).
  It is unaffected by BR-5 and must not be converted to `ft.Clipboard`. BR-5's
  count of 2 is the number of *Flet* clipboard calls, not the number of places
  the app copies.
- `tests_tab_view.py:567-577` sets a control's `border_color` to red on failure
  and back to `None` on pass — a BR-16 site.

The seven editable dropdowns here (`:139,149,167,177,187,204,223`) bind **no**
handlers, so BR-1 does not reach them.

## 3.6 Roots tab — `roots_tab_view.py`, 8 bindings

| Control | Event | What the user sees |
|---|---|---|
| root dropdown (`:38`) | change | **BR-1 site** — loads the selected root into the form |
| `New` (`:70`) | click | blank form for a new root |
| `Clear` (`:73`) | click | empties the form |
| `Delete` (`:168`) | click | opens a confirm dialog (`:375` confirm, `:376` cancel); `on_hover` turns it red |
| `Save` (`:178`) | click | writes the root back |

## 3.7 Sandhi tab — `sandhi_view.py`, 16 bindings

Five paired groups, each a set of fields plus a button, and in every group the
fields' `on_submit` and the button's `on_click` are **the same handler** — so
Enter in any field of a group does what its button does.

| Group | Fields | Button | Effect |
|---|---|---|---|
| sandhi OK | `:42` | `:50` | marks the word sandhi-checked |
| add to sandhi | `:57`, `:65` | `:73` | records word + construction |
| bulk add | `:80` | `:89` | adds many at once |
| variants | `:96`, `:104` | `:112` | records a variant |
| spelling mistakes | `:119`, `:127` | `:135` | records a spelling mistake |
| see-also | `:142`, `:150` | `:158` | records a "see" reference |

## 3.8 Bold Search tab — `bold_search_view.py`, 5 bindings

| Control | Event | What the user sees |
|---|---|---|
| search field 1 (`:53`) | submit | runs the search |
| search field 2 (`:64`) | submit | same |
| text filter (`:74`) | **change** | filters the results as you type — a keystroke path |
| `Search` (`:111`) | click | runs the search |
| `Clear` (`:115`) | click | empties the fields |

This view holds four of the seven breaking `ft.border.all` calls
(`:92,151,349,352`) and both `ft.Alignment.TOP_LEFT` sites (`:238,243`).

## 3.9 Migration notes for this section

- **BR-17:** all nine modules.
- **BR-1:** four sites here — the two Compound Type lambdas, the Filter preset
  dropdown, the Roots dropdown.
- **BR-16:** three of the four border-colour signals are in this section —
  filter validity, test failure, and the Bold Search borders.
- **BR-2 / BR-3:** Bold Search and Filter hold most of the breaking border and
  alignment sites, and the two `BorderSide` calls that must be left alone.
- **BR-8:** the Translations snackbar assignment, plus confirm dialogs in
  Compound Type, Filter and Roots.
- **Phase 4 / Phase 5:** the Global tab's four buttons are the priority — all
  long-running, all with mid-handler progress messages that stop painting under
  1.0. `Update Anki` alone has 5 s of hard sleeps plus a full updater run.
- **Generated wiring:** Compound Type's grid handlers and Filter's cell editors
  are built by factories. The inventory records the factory call site, so the
  Phase 7 diff will not show one line per cell.
- **Grep trap:** `gui2/build/site-packages/` contains a complete vendored copy
  of Flet 0.28. Any sweep must exclude it — `capture_wiring.py` and
  `check_self_page.py` both do.

---

# 4. Popups, shell and standalone windows

51 bindings. The app shell, the shared popup, four popup windows, two
find-replace tabs, and three standalone scripts.

## 4.1 The app shell — `gui2/main.py`, 9 bindings

| Control | Event | What the user sees |
|---|---|---|
| page (`:48`) | keyboard | the global handler — tab jumps, scrolling, Ctrl+Q/F/W/S, Ctrl+Shift+A. **BR-4** |
| `Submit Data` (`:65`) | click | runs the contributor data submission, then shows a dialog with the result |
| `Update` (`:70`) | click | shows a warning dialog about overwriting the local database, then on confirm pulls the latest code and shows a summary dialog |
| three dialog OKs (`:148`, `:165`, `:181`) | click | `lambda _: self.page.close(dialog)` — **BR-8**, and note `pop_dialog()` takes no argument, so these lambdas change shape, not just name |
| `Update` in the confirm dialog (`:185`) | click | `_run_update` — closes the confirm, runs the update inline, opens the result dialog |
| tabs (`:386`) | change **and** click | both bound to `_on_tab_activated`. **BR-14** — 1.0 has no `on_click` on `Tabs`, so the double binding collapses to one |

`Submit Data` and `Update` both run git operations inline — long actions with no
progress indicator, and `Update` can overwrite the local database.

The two appbar buttons appear **only** for a non-primary user who is not a
server contributor (`:58-61`). A primary user never sees them, so they are easy
to miss when testing.

### ⚠️ The warm-up worker hides BR-17, and BR-14 breaks the reporting

`build_ui` (`:416-417`) launches `_warmup_in_background` on a worker thread,
which builds **all 16 views** ahead of time (`:328-351`):

```python
for index in self._warmup_tab_order:
    try:
        self._ensure_tab_built(index)
    except Exception:
        failed.append(self._tab_label(index))
```

Three things compound here after the upgrade:

1. **BR-17 raises inside every view builder** — `self.page = page` in a
   `ft.Column` subclass.
2. **The `except Exception` discards the message**, keeping only the tab label.
   So the reason is thrown away; the user gets "Warm-up failed for: Global,
   Transl, …" with no cause.
3. **`_tab_label()` is itself broken by BR-14** (`:355`, `.tab_content` is gone).
   It is called *inside the except handler*, so its `AttributeError` is not
   caught — **the warm-up thread dies at the first failure** and no snackbar
   appears at all.

Net effect after the upgrade and before the fixes: the window opens, the first
tab renders, no "All tabs and tools ready" message ever arrives, and every other
tab is built on demand when clicked — where it raises again.

**So "the app starts" is not evidence BR-17 is fixed.** The verification is the
"All tabs and tools ready." snackbar plus opening every tab.

## 4.2 The shared popup — `gui2/mixins.py`, 2 bindings

`PopUpMixin` provides one reusable text-entry dialog, used by Pass1Add's three
add-to-X actions and by Sandhi.

| Control | Event | What the user sees |
|---|---|---|
| `Cancel` (`:50`) | click | closes, sets the result to `None`, and calls the caller's callback **with `None`** |
| `OK` (`:54`) | click | closes, sets the result to the typed value, and calls the callback with it |

Both paths call the callback, so a caller must handle `None` — Pass1Add's
`process_*_popup_result` handlers each check for it.

The dialog and its text field are built **once in `__init__`** and reused;
`show_popup` (`:81`) re-labels and re-values them each time. That single
long-lived dialog is a BR-13 frozen-control candidate — Phase 5 should watch it
specifically.

`show_popup` uses `page.open` (`:93`) — BR-8.

## 4.3 Word finder — popup and widget, 7 bindings

| Control | Event | What the user sees |
|---|---|---|
| popup search field (`:16`) | submit | searches |
| popup `Search` (`:27`) | click | searches |
| popup `Clear` (`:32`) | click | empties the results |
| popup `Close` (`:85`) | click | closes |
| widget search field (`:27`) | submit | searches |
| widget `Search` (`:38`) | click | searches |
| widget `Clear` (`:43`) | click | empties the results |

The popup is opened by Ctrl+F from anywhere, pre-filled with the current lemma
(`main.py:224`). Both modules hold a breaking `ft.border.all` call
(`wordfinder_popup.py:163`, `wordfinder_widget.py:109`).

## 4.4 AI search window — 4 bindings

A **separate Flet app** in its own window, launched by Ctrl+Shift+A
(`main.py:222`) via a subprocess.

| Control | Event | What the user sees |
|---|---|---|
| query field (`:41`) | submit | runs the AI query |
| model dropdown (`:48`) | **focus** | reloads the model list on focus — its only handler, so BR-1 does not touch it |
| reload icon (`:58`) | click | re-reads the models |
| its own page (`:168`) | keyboard | its own global handler, independent of the editor's |

Because it owns its own page and process, its keyboard handler never interacts
with BR-4's swap in Pass2Add.

## 4.5 Find-replace tabs — sandhi and spelling, 5 bindings each

Two tabs with identical shape (`'` and `Sp`, indices 8 and 9).

| Control | Event | What the user sees |
|---|---|---|
| find field (`:28` / `:27`) | **blur** | prepares the search from the typed value |
| `Find` (`:42` / `:41`) | click | runs the search and lists matches |
| `Clear` (`:43` / `:42`) | click | empties the search |
| `Commit` (`:57` / `:46`) | click | applies the replacement |
| `Ignore` (`:58` / `:47`) | click | skips this match |

Both also carry a `strip` switch (`sandhi:41`, `spelling:40`) that binds no
handler — read at commit time.

## 4.6 Test manager popup — `gui2/test_manager.py`, 5 bindings

Shown when a test fails during an add-to-database attempt.

| Control | What the user sees |
|---|---|
| `Edit` (`:85`) | opens the entry for editing |
| `Add Exception` (`:86`) | records this result as an allowed exception |
| `Next Failure` (`:87`) | moves to the next failing test |
| `Close` (`:88`) | dismisses |
| `Open Test File` (`:89`) | opens the tests file externally — subprocess |

`tests_tab_controller.py:801,802` is a further OK/Cancel confirm dialog.

## 4.7 Username dialog — `gui2/user.py`, 2 bindings

| Control | Event | What the user sees |
|---|---|---|
| username field (`:25`) | submit | saves the username and closes |
| `Save` (`:41`) | click | same |

Asked once at startup (`main.py:137`). The stored username drives the
`comment` field's "Add a comment" requirement (§1.4) and whether the appbar's
`Submit Data` / `Update` buttons exist at all.

## 4.8 Standalone utilities — 10 bindings, Phase 6 scope

Two scripts under `gui2/utilities/`, each its own `ft.app` entry point.

| Script | Controls |
|---|---|
| `find_words_with_examples.py` | its own keyboard handler (`:87`), then `Yes` / `No` / `Pass` / `Reset` (`:103-106`) |
| `sandhi_contraction_find_replace_gui.py` | keyboard handler (`:95`), then `Find` / `Clear` / `Commit` / `Ignore` (`:100-110`) — the same four as §4.5 |

Both assign `self.page` on a **plain** class, so **neither needs BR-17 work**.
Both need BR-6 (`ft.app` → `ft.run`) and BR-7.

## 4.9 Migration notes for this section

- **BR-4:** `main.py:48` is the site; `ai_search_window.py:168` and the two
  utilities bind their own independent handlers and are unaffected by the swap.
- **BR-8:** `main.py:148,165,181` pass the dialog to `page.close(...)`;
  `pop_dialog()` takes no argument, so these three lambdas change shape.
  `mixins.py:93` uses `page.open`.
- **BR-13:** `PopUpMixin`'s dialog is built once and reused for the life of the
  app — the strongest frozen-control candidate found so far.
- **BR-14:** `main.py:386`'s double `on_change` + `on_click` binding, and
  `_tab_label()` inside the warm-up's except handler.
- **BR-17:** `main.py`, `wordfinder_popup.py`, `ai_search_window.py`, `user.py`,
  `test_manager.py` and both utilities are all **plain classes** — none needs
  the fix. Only `sandhi_find_replace_view.py` and
  `spelling_find_replace_view.py` from this section are in the 23.
- **Phase 4:** `Submit Data` and `Update` run git inline; the AI search window
  and the test-file opens are subprocesses.
- **Testing trap:** the appbar's two buttons only render for a non-primary,
  non-server-contributor user.
