# Plan — TH/THI chapter.verse sutta codes

## Phase 1 — Implement
- [x] Edit `tools/sutta_codes.py::make_list_of_sutta_codes`: add THAG→TH /
  THIG→THI synthetic alias inside the `not is_vagga and not is_samyutta` block.
  → verify: smoke check prints `['TH1.45', 'TH45', 'THAG1.45']` ✅

## Phase 2 — Lookup rebuild (user-run)
- [ ] User runs `uv run python -m db.suttas.suttas_to_lookup`
  → verify: `Lookup.lookup_key == "TH1.45"` resolves same headwords as `TH45`
