# Spec: Remove ORM mutation in grammar_to_lookup.py

**GitHub:** #157

## Overview

`db/grammar/grammar_to_lookup.py` temporarily mutates `DpdHeadword.pos` in memory
(lines 68–86 via `modify_pos`) to reclassify parts of speech for grammar data
generation. Because these are tracked ORM objects, SQLAlchemy's autoflush writes
the mutations to the database on the next query — before `g.close_db()` can roll
them back. The close/rollback is therefore a fragile workaround for a self-inflicted
problem: mutating objects that were never meant to be changed.

## What it should do

Instead of mutating `i.pos` on loaded `DpdHeadword` objects, `modify_pos` should
return a `dict[int, str]` mapping `headword.id → overridden_pos` for only the words
whose pos classification changes. `generate_grammar_data` reads from this dict (with
`i.pos` as fallback) instead of reading the mutated attribute.

With no ORM objects ever dirtied, there is no need to close or roll back the session.
`GlobalVars.close_db()` and `commit_db()` can both be removed, along with the call
to `g.close_db()` in `main()`.

## Constraints

- The grammar data written to the Lookup table must be identical to what it was
  before — only the mechanism for holding the temporary pos values changes.
- `g.db_session` must remain open through `add_to_lookup_table(g)`.

## How we'll know it's done

- `grammar_to_lookup.py` runs without errors when the grammar config gate is enabled.
- No `DpdHeadword` rows are modified in the database after the script runs.
- `uv run pytest tests/ -k grammar` passes (or shows no regressions if no tests exist).

## What's not included

- Changing `modify_pos()` logic — same classification rules, different output form.
- Touching `sync_lookup_column` — that's a separate thread.
- Changing `generate_grammar_data` behavior beyond the pos lookup mechanism.
