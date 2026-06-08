# Spec: Isolate `sync_lookup_column` session

**GitHub:** #157

## Overview

`sync_lookup_column()` in `tools/lookup_sync.py` calls `db_session.expunge_all()` inside its chunk loop to control memory when processing the ~1.3M-row Lookup table. This detaches *all* ORM objects from the session passed by the caller — not just the Lookup rows the function itself loaded. Any caller that loads ORM objects before calling `sync_lookup_column` and accesses them afterward will hit `DetachedInstanceError`.

This just broke `db/families/family_root.py`: it loaded `DpdRoot` objects, called `update_lookup_table` → `sync_lookup_column` → `expunge_all()`, then tried to iterate the detached `DpdRoot` list in `generate_root_info_html`. The workaround (swap call order) papers over the symptom but doesn't fix the root cause.

## What it should do

Give `sync_lookup_column` its own isolated SQLAlchemy session, derived from the caller's session bind. The `expunge_all()` inside the chunk loop then only affects that private session — the caller's session remains untouched.

No changes to the function's signature, return type, behavior, or its 9 call sites. No workarounds needed in any caller.

## Assumptions & uncertainties

- `db_session.get_bind()` returns a valid engine in all contexts this function is called (build scripts, tests). All callers pass sessions backed by SQLite engines — this is safe.
- Creating a short-lived `Session(bind=...)` inside the function and closing it doesn't introduce any SQLite threading issues. SQLAlchemy's `Session` is not threadsafe, but this function is called synchronously within a single thread at each call site — also safe.
- The `clear_stale` pass and the chunk loop can share the same private session.
- The call-order workaround already applied in `family_root.py` (swapping `generate_root_info_html` before `update_lookup_table`) should be reverted once this fix lands.

## Constraints

- Signature and behavior must not change — 9 call sites + tests rely on it.
- The internal session must commit independently so the caller can still see updated rows when they re-query.

## How we'll know it's done

- `db/families/family_root.py` runs end-to-end (or its unit tests pass) with the original call order restored: `update_lookup_table` before `generate_root_info_html`.
- All existing `tests/tools/test_lookup_sync.py` tests pass unchanged.
- No other caller breaks (verified by running relevant test suites).

## What's not included

- Removing `expunge_all()` entirely — still needed for memory control.
- Changing the `sync_lookup_column` API — no new params, no return type changes.
