# Spec: Book Code Translator

## Overview
Build a single source of truth and translator for book identifiers used across DPD. Today these mappings are scattered across at least 4 files: `tools/pali_text_files.py` (`cst_texts`), `gui2/dpd_fields_examples.py` (`book_codes`), `shared_data/help/abbreviations.tsv`, and `db/bold_definitions/functions.py` (`file_list`). Adding a new book requires editing several of them in lockstep — `MEMORY.md` already records one instance of this drift.

## Reference
No GitHub issue.

## What it should do
A new module `tools/cst_book_translator.py` backed by a new file `tools/cst_book_translator.tsv` (co-located, matching the `tools/ipa.py` + `tools/ipa.tsv` convention). Inputting any one of the four identifier types returns the others when defined.

Four input types:
1. **CST filename stem** — `s0101m.mul` (corresponds to `resources/dpd_submodules/cst/romn/s0101m.mul.xml`)
2. **CST book name** — `Dīghanikāya, Sīlakkhandhavaggapāḷi` (nikāya + book, comma-joined)
3. **GUI book code** — `dn1` (as used in `cst_texts` keys and `gui2/dpd_fields_examples.py`)
4. **DPD book code** — `DN` / `DNa` / `DNt` (as used in `shared_data/help/abbreviations.tsv` and `bold_definitions/functions.py::file_list`)

Cardinality (discovered from existing dicts):
- 1 CST filename → at most 1 GUI code, at most 1 DPD code, exactly 1 CST book name
- 1 GUI code → 1+ CST files (e.g. `kn14` → 2 files, `abh6` → 3 files, `abh7` → 5 files)
- 1 DPD code → 1+ CST files (e.g. `VINa` → 5 files)
- 1 CST book name → 1 CST file

Canonical row key: **CST filename**. Translator returns a list for inputs that fan out.

## Public API (tools/cst_book_translator.py)
```python
@dataclass(frozen=True)
class BookInfo:
    cst_filename: str            # e.g. "s0101m.mul" (stem, no .xml)
    cst_book_name: str           # e.g. "Dīghanikāya, Sīlakkhandhavaggapāḷi"
    gui_book_code: str | None    # e.g. "dn1"
    dpd_book_code: str | None    # e.g. "DN"

    @property
    def cst_xml_path(self) -> Path: ...

def all_books() -> list[BookInfo]: ...
def from_cst_filename(stem: str) -> BookInfo | None: ...
def from_gui_code(gui_code: str) -> list[BookInfo]: ...
def from_dpd_code(dpd_code: str) -> list[BookInfo]: ...
def from_cst_book_name(name: str) -> list[BookInfo]: ...
def translate(value: str) -> list[BookInfo]: ...
```

Case-insensitive comparison on GUI/DPD codes and book name; CST filename stems already lowercase.

## Data file (tools/cst_book_translator.tsv)
One row per CST `.xml` file. Tab-separated, header row:
```
cst_filename	cst_book_name	gui_book_code	dpd_book_code
```
Empty cells where mapping does not exist. Generated initially by merging the three existing source dicts.

## Assumptions & uncertainties
- **BJT mappings out of scope.** `db/variants/files_to_books.py::bjt_files_to_books` is a different corpus.
- **Existing call-sites untouched.** Migration is a future thread.
- **`abbreviations.tsv` not touched.** Has many DPD codes that aren't book codes.
- **CST book names** derived from `book_codes` display strings (in `gui2/dpd_fields_examples.py`), with nikāya prefix prepended.
- **Row set = union of `cst_texts` ∪ `book_codes` ∪ `file_list`.** Files in `resources/dpd_submodules/cst/romn/` not appearing in any of the three are not included in this initial pass.

## Constraints
- No new runtime dependencies. Stdlib `csv`.
- No `sys.path` hacks.
- Modern type hints (`list[BookInfo]`, `str | None`).
- TSV loaded once at module import; subsequent lookups are dict reads.

## How we'll know it's done
- `tools/cst_book_translator.tsv` exists with one row per CST file across the three source dicts.
- `tools/cst_book_translator.py` exposes the API above.
- `tests/tools/test_book_translator.py` covers round-trips, fan-out, auto-detect, unknown inputs.
- `uv run pytest tests/tools/test_book_translator.py` passes.
- `uv run ruff check tools/cst_book_translator.py tests/tools/test_book_translator.py` passes.

## What's not included
- BJT file mappings.
- Migrating `cst_texts`, `book_codes`, `file_list`, or any call-site.
- Touching `shared_data/help/abbreviations.tsv`.
- Extracting book names from XML.
- A CLI wrapper.
