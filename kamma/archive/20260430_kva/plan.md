---
thread: 20260430_kva
---

## Architecture Decisions
- Reused `g.is_api` (commentary mode flag) and `g.is_bhikkhuni` from `GlobalData` — no new state fields needed.
- `g.section` stores the current uddesa/kaṇḍa name; `g.vagga` stores vagga name — same pattern as `vina_commentary`.
- `vin04t.nrf.txt` stays in `vint`; `kva` gets its own `cst_texts` entry pointing to the same file — no duplication risk since they serve different lookup purposes.
- `books.py` `SuttaCentralSource` entry uses `cst_books=["kva"]` (not the raw filenames) so `make_cst_text_list` resolves through `cst_texts`.

## Phases

### Phase 1 — Register book key
- [x] Add `"kva": ["vin04t.nrf.txt"]` to `cst_texts` in `tools/pali_text_files.py`
  → verify: `get_cst_filenames("kva")` returns `["vin04t.nrf.txt"]`

### Phase 2 — Implement handler
- [x] Add `kva_dvemātikā_kaṅkhāvitaraṇī(g)` to `tools/cst_source_sutta_example.py`
- [x] Wire `case "kva":` into `find_cst_source_sutta_example` match block
  → verify: function callable without error

### Phase 3 — Test
- [x] Update `__main__` block with 8 XML-sourced test cases; all PASS
  → verify: `uv run python tools/cst_source_sutta_example.py` — all `[PASS]`

### Phase 4 — gui2 integration
- [x] Add `"KVA dvemātikāpāḷi + kaṅkhāvitaraṇī": "kva"` to `book_codes` in `gui2/dpd_fields_examples.py`
- [x] Add `SuttaCentralSource("kva", ["kva"], None, None)` to `sutta_central_books` in `gui2/books.py`
  → verify: KVA appears in gui2 dropdown and returns results (confirmed by user)
