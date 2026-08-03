# Plan — Anandajoti word import via the X button

## Tasks

- [x] 1. `gui2/paths.py`: add `pass2_x_words_path` (`gui2/data/pass2_x_words.json`);
      remove `pass2_x_manager_py_path` (only consumer was the importlib reload being deleted).
      → verified: `rg -n "pass2_x_manager_py_path"` — no live code hits.

- [x] 2. `gui2/pass2_x_manager.py`: replace the SQL `filter_query` + id-deque with a
      JSON-backed queue (`load_data` / `save_data` atomic write / `get_next` /
      `requeue` / `remaining_count`), modelled on `Pass2EgManager`.
      → verified: ruff + pyright clean; drained 46/46 entries in a scripted run.

- [x] 3. `gui2/pass2_add_view.py`: rewrite `_click_x_button` — pop the next entry, pop
      `comment`, update mode when `id` present (db fields + proposals into `_add`),
      new-word mode otherwise (values into base fields). Dropped the importlib block.
      `Pass2XManager(self.toolkit)`. Tooltip "filter queue" → "import queue" (both the
      static tooltip and the hover count label).
      → verified: ruff clean; `gui2/` is pyright-excluded.

- [x] 4. Author `gui2/data/pass2_x_words.json` — 46 entries: 6 updates
      (`doha` 89897, `uttama 1` 14631, `aññātāvī 1.1` 1629, `aññātāvī 2.1` 1630,
      `anuggata` 4408 renumber, `hīyattanī` 71360) + `doha 2` new + 25 §7b metres
      + 14 §8a grammar terms.
      → verified by script against live `dpd.db`: every key is a real column, every
      `pattern` exists in `inflection_templates`, `root_key √duh` exists in `dpd_roots`,
      all 6 ids resolve, no new `lemma_1` collides with an existing one.

- [x] 5. `.gitignore`: `/gui2/data/pass2_x_words.json` (+ `.tmp`) next to `pass2_eg_words.json`.

- [x] 6. Full gate: ruff check + format + pyright on touched files, `just typecheck`
      (0 errors), `uv run pytest tests/` (1768 passed, 12 deselected).

## Notes / drift log

- **Part I was already largely entered in the db** (ids 89894–89899) before this thread —
  so Part I contributes updates, not new words. Recorded in `spec.md`.
- **`hīyattanī` (71360) already covers §8a #16 `hiyattana`**, and **`muddhaja 2` (53006)
  already carries §8a #8** — so §8a yields 14 new entries, not 16, and `hiyattana`
  became an update (var_text) rather than a new headword.
- **Added `requeue()`** beyond the plan: `get_next()` pops *and* rewrites the file, so a
  failed load (missing id, exception) would silently destroy the entry. `_click_x_button`
  now puts it back on both failure paths.
- **`VUTT<n>` source codes from the note were not used** — the db cites grammar works as
  lowercase free text (`kaccāyana`, `bālāvatāra`, `padarūpasiddhi`), so the queue uses
  `vuttodaya`, `saddanīti`, `moggallānapañcikā`, `niruttidīpanī`, `abhidhānappadīpikā`.
- **Two more updates added (now 48 entries: 8 updates + 40 new)**, found by re-reading the
  already-entered Part I rows against the note:
  - `pādayuga 2` (89895) — has no source/example; the note supplies the Vuttodaya prosody
    quote (`saññāparibhāsāniddesa`: *ādima'matha pādayugaṃ, yassā tyaṃ'sehi sā pathyā*).
  - `dīpaka 1.2` (89899) — complete otherwise; the note adds `synonym vītaṃsa` and the
    Cone/PED/MW/Edgerton etymology debate for `notes`. The editor already chose
    `sanskrit = dīpaka [dīp]`, so this is a proposal only.
- **Review outcome — CodeRabbit (3 findings, all `pass2_x_manager.py`):**
  - *accepted* — validate on load that the JSON decodes to a mapping of lemma to field
    dicts. Worth it because the file is hand-authored and swapped per batch; verified it
    rejects a list and a non-dict entry, and still accepts valid data.
  - *rejected* — interprocess lock around reload/mutate/replace. `Pass2EgManager`, the
    sibling this copies, has none; the X button is a single-editor scratch slot.
    An interprocess lock would be more machinery than the whole feature.
  - *rejected* — roll back the in-memory pop when `save_data` fails. If the write fails
    the file still holds the entry, so it is re-served on the next load: the failure mode
    is repeated work, not lost data, which is the safe direction.
- **Compound fields deliberately left empty** on the §7b/§8a entries
  (`construction`, `compound_type`, `compound_construction`): filling them needs
  per-word lexicographic judgement, and a wrong value costs more to undo than to type.
