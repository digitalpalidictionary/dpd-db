# Plan — Proofreader multi-field

## Tasks

- [x] 1. `tools/paths.py`: add path attrs for the two new TSVs + caches.
      → verify: `python -c "from tools.paths import ProjectPaths; ..."` attrs exist.

- [x] 2. `tools/proofreader.py`: generalize the pipeline over a field config.
      - `ProofreadField` dataclass (name, tsv_path, cache_path, context_field, filter kind).
      - `get_db_data(session, field=..., context_field=..., only_empty_meaning_1=...)`.
      - `construct_prompt(batch, field="meaning_1", context_field=None)` — meaning_lit
        variant includes meaning_1 context + "do not make idiomatic".
      - `build_corrected_by_id(batch, field=...)`, `apply_checked_item(..., field=...)`.
      - `process_batch(..., field=..., context_field=...)`.
      - Extract per-field loop into `run_field(...)`; `main()` runs all three
        (optional `--field` arg to run one).
      - Keep existing single-arg call signatures working via defaults (existing tests).
      → verify: `uv run pytest tests/tools/proofreader/`.

- [x] 3. `tools/proofreader.py`: rework `ProofreaderManager` to cycle the three
      queues. Constructor takes `list[tuple[str, Path]]`; `get_next_correction`
      returns `(row | None, remaining, field | None)`; `count` sums all queues.
      Reuse module `load_tsv_queue`/`save_tsv_queue`/`tsv_lock`.
      → verify: manager test updated + green.

- [x] 4. `gui2/toolkit.py`: build the three-queue list from `project_paths`.
      `gui2/pass2_add_view.py`: unpack the 3-tuple, load into `field`.
      → verify: `uv run pyright gui2/toolkit.py gui2/pass2_add_view.py`.

- [x] 5. Tests: update existing (manager 3-tuple), add meaning_lit prompt +
      meaning_2 filter + queue-cycling coverage.
      → verify: `uv run pytest tests/tools/proofreader/`.

- [x] 6. `justfile`: update the `proofread` comment to mention all three fields.

- [x] 7. Lint gate on every touched file + full proofreader suite. Review. Finalize.
