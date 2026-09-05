# Anki: stale root fields when a word stops being root-derived

## Problem

When a headword changes from root-derived to a compound (its `root_key` is cleared
in the db), the Anki note keeps the old root data.

## Cause

In `exporter/anki/anki_updater.py`, `update_note_values()` writes every note field
unconditionally **except** seven, which sit inside `if i.root_key:`:

```python
    if i.root_key:
        note["sanskrit_root"] = str(i.rt.sanskrit_root)
        note["sanskrit_root_meaning"] = str(i.rt.sanskrit_root_meaning)
        note["sanskrit_root_class"] = str(i.rt.sanskrit_root_class)
        note["root_meaning"] = str(i.rt.root_meaning)
        note["root_in_comps"] = str(i.rt.root_in_comps)
        note["root_has_verb"] = str(i.rt.root_has_verb)
        note["root_group"] = str(i.rt.root_group)
```

The guard is needed — `i.rt` is `None` without a root key — but there is no `else`,
so on the empty-root path those seven fields are simply left at their previous
values. (`root_key`, `root_sign`, `root_base` are fine: they are set from plain
columns/`root_clean`, which return `""`.)

Because the note is otherwise updated, `is_updated` is True and the note is
flushed with the stale root fields intact.

## Simplest fix

Add an `else` that blanks the same seven fields:

```python
    else:
        note["sanskrit_root"] = ""
        note["sanskrit_root_meaning"] = ""
        note["sanskrit_root_class"] = ""
        note["root_meaning"] = ""
        note["root_in_comps"] = ""
        note["root_has_verb"] = ""
        note["root_group"] = ""
```

No other change required. Existing already-corrupted cards self-heal on the next
update run, because the fields become unconditionally written.

## Verify

`uv run pytest tests/exporter/anki/test_anki_updater.py` plus a new case: a note
carrying root values, updated from a headword with no `root_key`, ends with all
seven root fields empty.
