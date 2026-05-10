# Plan: Pass2Add "X" filter-queue button

## Architecture decisions
- **New file `gui2/pass2_x_manager.py`** holds the editable filter function at the top and a small `Pass2XManager` class wrapping the queue.
- **Filter signature** — `filter_query(db_session) -> list[int]` returning headword IDs.
- **Queue stored in the manager**, not the view. View just calls `get_next()` → `(headword_id | None, remaining)`.
- **Auto-refill on empty** — re-run filter once when the queue runs out.

## Phase 1: Manager and filter file
- [ ] Create `gui2/pass2_x_manager.py` with `filter_query(db) -> list[int]` and `Pass2XManager` class.
  → verify: `uv run ruff check gui2/pass2_x_manager.py` passes.

## Phase 2: Wire button into Pass2Add view
- [ ] Edit `gui2/pass2_add_view.py`: import + instantiate manager, add `_x_button`, insert into toolbar row, add `_click_x_button`.
  → verify: `uv run ruff check gui2/pass2_add_view.py` passes; module imports without error.

## Phase 3: End-to-end check
- [ ] User launches GUI2, opens Pass2Add, clicks X.
  → verify: button between Add and PRead; loads matching headword; shows remaining; empty case shows "No more X words".
