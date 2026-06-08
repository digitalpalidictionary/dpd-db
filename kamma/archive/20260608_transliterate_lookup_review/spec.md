# Spec: review transliterate_lookup_table.py (likely no helper migration)

## GitHub issue
#157 Refactoring (lookup_sync rollout — disposition of the last deferred script)

## Recommendation up front
**Do not migrate `db/lookup/transliterate_lookup_table.py` onto `sync_lookup_column`.**
It does not fit the helper's model, and forcing it adds churn for no benefit. This thread
exists to record that decision and to fix the one thing that *is* worth fixing — a likely
boolean-precedence bug.

## Why it does not fit the helper
1. **Update-only.** It never adds or deletes Lookup rows; it only fills `sinhala`,
   `devanagari`, `thai` on rows that already exist. It does not use `update_test_add` at
   all — so it is not part of the DRY target the helper addresses.
2. **Three columns per key.** The helper is single-column. Migration would mean either
   three passes (3× `sync_lookup_column` with `clear_stale=False`) or a brand-new
   multi-column abstraction.
3. **The full-table load is intrinsic, not waste.** It transliterates *every* lookup key
   (`query(Lookup).all()` → batched across processes). Scoping to "rows that changed"
   makes no sense — there is no incoming `{key: value}` dict; the values are *computed*
   from every key. So the scoped-query perf win does not apply.
4. **Its `is_another_value` use is unrelated.** `is_another_value(i, "epd")` is a
   heuristic to skip transliterating pure-English (EPD) entries — not delete routing.

## The real issue to fix: boolean precedence in `_parse_batch`
The per-row filter reads:

```python
if (
    not i.sinhala
    or regenerate_all
    and not is_another_value(i, "epd")
):
```

`and` binds tighter than `or`, so this parses as
`(not i.sinhala) or (regenerate_all and not is_another_value(i, "epd"))`.

That means when a row has **no** sinhala yet, it is selected for transliteration
**regardless of the EPD check** — so pure-English rows with no sinhala still get
transliterated. The likely intent is
`(not i.sinhala or regenerate_all) and is_another_value(i, "epd")` — i.e. always skip
EPD-only rows. (Note: `is_another_value(i, "epd")` returns True for rows with real
non-EPD data; the `not` must be removed.)

## Options
- **(a) Recommended:** leave the write path as-is (no helper). Fix the precedence bug if
  confirmed. Optional tidy: type hints, remove dead commented-out lines
  (`# sinhala_translit_set.remove("")` etc.), `Path` usage for the temp json files.
- **(b) If uniformity is strongly wanted:** introduce a sibling
  `update_lookup_columns(db, {key: {col: value}}, *, clear_stale=False)` in
  `tools/lookup_sync.py` for update-only multi-column writes, and route transliterate's
  write-back through it. Higher effort, debatable value — decide explicitly.

## Constraints
- Behaviour-preserving unless the precedence fix is explicitly approved (it changes which
  rows get transliterated).
- Modern type hints, pathlib, `pr` printer.

## Done when
- A decision is recorded (migrate vs leave).
- The precedence behaviour is confirmed and either fixed (with a test) or documented as
  intended.
- Any cleanup gated: `ruff check --fix` → `ruff format` → `pyright` → `pytest`.

## Not included
- The single-column lookup_sync migration (this script is the exception).
