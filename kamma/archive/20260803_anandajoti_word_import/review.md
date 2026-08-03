# Review — Anandajoti word import via the X button

**Verdict: PASSED** — confirmed working in a live gui2 session by the user, 2026-08-03.

## What changed

- `gui2/pass2_x_manager.py` — rewritten: JSON-backed import queue replacing the SQL
  `filter_query` id-deque. `load_data` (with shape validation) / `save_data` (atomic) /
  `get_next` (reloads from disk, archives what it pops) / `requeue` / `remaining_count`.
- `gui2/pass2_add_view.py` — `_click_x_button` rewritten; importlib live-reload removed;
  `Pass2XManager(self.toolkit)`; tooltip and hover-count label say "import queue".
- `gui2/paths.py` — `pass2_x_words_path` + `pass2_x_words_done_path` added,
  dead `pass2_x_manager_py_path` removed.
- `gui2/data/pass2_x_words.json` — new, gitignored: 48 entries (8 updates, 40 new).
- `.gitignore` — queue file, its `.tmp`, and the done-archive.

## Reviews run

Two independent passes in parallel: CodeRabbit (external) and a from-scratch adversarial
audit. The audit stalled mid-stream on an API error and was resumed from its transcript.

### CodeRabbit — 3 findings, all `pass2_x_manager.py`

| Finding | Outcome |
|---|---|
| Validate the JSON decodes to a mapping of lemma → field dict | **fixed** — verified it rejects a list and a non-dict entry, still accepts valid data |
| Interprocess lock around reload/mutate/replace | **rejected** — `Pass2EgManager`, the sibling this copies, has none; X is a single-editor scratch slot, and a lock would be more machinery than the feature |
| Roll back the in-memory pop when `save_data` fails | **rejected** — on a failed write the file still holds the entry, so it is re-served next load: repeated work, not lost data |

### Independent audit — findings and outcomes

| # | Finding | Outcome |
|---|---|---|
| 1 | Swapping the queue file while the app runs served the **stale in-memory dict** and wrote it back, destroying the new batch. `load_data` only ran in `__init__`, and `Pass2AddView` is built once at warm-up. | **fixed** — `get_next` and `remaining_count` reload from disk first. Verified: pop, swap the file mid-session, next click serves the new batch. |
| 2 | An entry was drained on click, before any save — a misclick or abandoned entry destroyed hand-authored text that exists nowhere else (file is gitignored). | **fixed** — every popped entry is copied to `pass2_x_words_done.json`. Verified both pops land in the archive. |
| 3 | `verb = "√duh"` / `"√druh"` — `verb` is a closed vocabulary, and on the new-word path it reached the base field, so a save would have written it to the db. | **fixed** — dropped from both `doha` entries; `doha 2`'s `derivative: kita` dropped too, since `√druh` is not in `dpd_roots` to hang it on. |
| 4 | All 39 gram/prosody entries omitted `family_set`, against 793/793 precedent. | **fixed** — `grammatical terms` on all 39. |
| 5 | `source_1` set with `example_1` empty on 38 entries — 0 precedent in 50,421 rows. | **fixed** — work name moved into `notes`, `source_1`/`sutta_1` cleared where there is no citable passage (217 `(gram)` rows do exactly this). |
| 6 | Seven `source_1` labels had no db precedent; `moggallānasutta` read as a sutta name, not a grammar work. | **fixed** by #5 — the labels now live in `notes` prose. |
| 7 | `lemma_2` was a copy of `lemma_1` on 12 masc/nt entries; it is the nominative singular. | **fixed** — `-o` for `a masc`, `-aṃ` for `a nt`. |
| 8 | `anajjatanī` declension vs its cited evidence; `aniyatakāla` unattested as a bare noun. | **anajjatanī kept** — `ajjatanī` (1231) and `hīyattanī` (71360) are both `ī fem` with `family_set grammatical terms`, so the ī-feminine is the established DPD form for tense names; note rewritten to say so. **`aniyatakāla` flagged in its `comment`** — db has only the adj `aniyatakālika` (72983); left for the editor rather than silently changed. |
| 9a | `remaining` computed before the requeue, reporting a count one too low. | **fixed** — computed after. |
| 9b | Exception path gave no sign the entry was requeued. | **fixed** — message names the requeued word. |
| 9c | A non-numeric `id` silently fell through to new-word mode with the id discarded. | **fixed** — reports the bad id and requeues. |
| 9d | Annotation `dict[str, dict[str, str]]` vs int ids in the JSON. | **not applicable** — all 8 ids are quoted strings; annotation is accurate. |
| 9e | `notes: no starting capital` fires on every entry. | **not fixed, by decision** — see below. |

### db_tests fires — deliberately not chased

Replaying `DbTestManager.run_all_tests_on_headword` over all 40 new-word entries leaves
these firing: `notes: no starting capital` (40), `derived_from is empty – nouns` (39),
`grammar: ana aṇa … no act` (5), `meaning_lit: ends in tā, no state` (4),
`neg: starts with an, no neg` (3), and one each of `construction: no plus`,
`root: nt aṇa`, `su: add to construction`.

The user's call: these are the editor's per-word checklist, not import defects, and they
were never going to pass on a bulk import. Clearing `derived_from` alone would mean
deciding `compound_type` and `construction` for 30-odd words — lexicographic judgement
this thread deliberately leaves to the editor. A control run over comparable rows already
in the db (`ajjatanī` 1231, `muddhaja 2` 53006, `hīyattanī` 71360, `ajjatanīvibhatti` 1232)
fires its own tests too, which confirms these are not clean-slate rules.

## Verification

| Check | Result |
|---|---|
| `ruff check` + `ruff format --check` on all touched files | clean |
| `uv run pyright gui2/pass2_x_manager.py gui2/paths.py` | 0 errors (`gui2/` is pyright-excluded, so `pass2_add_view.py` is ruff-only) |
| `just typecheck` (pyrefly, whole repo) | 0 errors |
| `uv run pytest tests/` | 1768 passed, 12 deselected |
| queue drain on a copy of the real file | 48/48 entries, 8 updates + 40 new |
| batch-swap-mid-session, archive, requeue, reload | all pass |
| load-time shape guard | rejects a list and a non-dict entry, accepts valid data |
| data vs live `dpd.db` | every field a real column, every `pattern` in `inflection_templates`, `root_key √duh` in `dpd_roots`, all 8 ids resolve, no new `lemma_1` collides |

**Not verified:** the button in a running gui2 session — that needs an interactive pass.
Pāḷi spellings and attestations were checked against `dpd.db` only, not the CST XML.

## Not tested, by design

No test pins down `Pass2XManager` or `_click_x_button`. The X button is a throwaway scratch
slot: the queue file is gitignored and swapped per batch, so any test would be rewritten
with the next batch. Recorded in `spec.md` and in the manager's docstring.
