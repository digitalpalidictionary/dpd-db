# Plan: Fix remove_brackets spacing

## Tasks
- [x] Reproduce on real CST example data (DB query + regex)
- [x] Fix `remove_brackets()` in `gui2/dpd_fields_functions.py`
- [x] Add regression test `tests/gui2/test_dpd_fields_functions.py`
- [x] Run ruff check/format + pyright + pytest on touched files
- [x] Review (PASS — see review.md)
- [x] Finalize

## Fix
```python
def remove_brackets(text: str) -> str:
    """Remove all content within square brackets [like this]."""
    text = re.sub(r"\s*\[[^]]*\]\s*", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,.;:!?])\s*(?=[^\s\d])", r"\1 ", text)
    return text.strip()
```
- 1st sub: existing bracket removal.
- 2nd sub: no space before punctuation.
- 3rd sub: exactly one space after punctuation — `(?=[^\s\d])` lookahead skips
  a digit so `1.55` / `3.364` are not split, and skips end-of-string so no
  trailing space is added.
- `strip()`: handle leading/trailing brackets.
- Ellipsis `…` is deliberately not in the punctuation set, so `… pe …` is kept.
