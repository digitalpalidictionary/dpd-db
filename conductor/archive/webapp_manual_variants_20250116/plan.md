# Plan: Webapp Manual Variants Support

## Overview
Add support for manual variant readings from `variant_readings.tsv` to the webapp, matching GoldenDict behavior.

## Refactoring Note
The existing `gui2/variants.py::VariantReadingFileManager` will be generalized into `tools/variants_manager.py` for reuse by both GUI2 and webapp.

## Phases

### Phase 1: Investigation & Understanding

- [x] Task: Read and understand current variant handling in `exporter/webapp/toolkit.py`
- [x] Task: Check `variant_readings.tsv` structure and content
- [x] Task: Review how GoldenDict exports manual variants (`exporter/goldendict/export_variant_spelling.py`)
- [x] Task: Review existing `gui2/variants.py::VariantReadingFileManager`
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

### Phase 2: Create Generalized variants_manager.py

- [x] Task: Create `tools/variants_manager.py` with:
  - `VariantManager` class - generalized, reusable variant file manager
  - `load()` - loads TSV into memory
  - `get_variants()` - returns full dict {variant: main}
  - `get_variant(main_word)` - reverse lookup: find variant by main form
  - `get_main(variant)` - forward lookup: find main by variant
  - `get_all()` - returns all variants dict
- [x] Task: Update `gui2/variants.py` to import from `tools.variants_manager`
- [x] Task: Write tests for `VariantManager` functionality
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

### Phase 3: Integrate Manual Variant Check into Webapp Search

- [x] Task: Modify `exporter/webapp/toolkit.py::make_dpd_html()`:
  - After DB variant check fails, check manual variants from `VariantManager`
  - Use cached instance (load once at module level)
- [x] Task: Create `ManualVariantData` class in `exporter/webapp/data_classes.py`
- [x] Task: Write integration tests for manual variant lookup
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

### Phase 4: Add Manual Variant Rendering

- [x] Task: Create template `exporter/webapp/templates/manual_variant.html` with format:
  ```html
  <h3 id="variants: {{ d.headword|safe }}">variants: {{ d.headword|safe }}</h3>
  <div class="dpd">
      <p>
          variant reading of <b><i>{{ d.main|safe }}</i></b>
      </p>
  </div>
  ```
- [x] Task: Add summary template for manual variants
- [x] Task: Modify toolkit.py to render manual variants when found
- [x] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)

### Phase 5: Testing & Verification

- [x] Task: Test with variants from issue #172 test cases:
  - `pāṇamatimāpayato` → `pāṇamatipātayato`
  - `paṇḍumuṭīkassa` → `paṇḍupuṭakassa`
  - `celaṇḍukena` → (check main form)
- [x] Task: Run `uv run pytest` to verify no regressions
- [x] Task: Run `uv run ruff check .` for linting
- [x] Task: Conductor - User Manual Verification 'Phase 5' (Protocol in workflow.md)

## Test Cases

```python
# tests/test_variants_manager.py

def test_variant_manager_loads_variants():
    """Test that variant_readings.tsv is loaded correctly."""
    vm = VariantManager()
    variants = vm.get_all()
    assert "celaṇḍukena" in variants
    assert variants["pāṇamatimāpayato"] == "pāṇamatipātayato"

def test_variant_manager_reverse_lookup():
    """Test reverse lookup by main form."""
    vm = VariantManager()
    # If we know the main form, find the variant
    main_form = "celapaṭikaṃ"
    variants = vm.get_all()
    for variant, main in variants.items():
        if main == main_form:
            assert variant == "celapattikaṃ"
            break

def test_manual_variant_lookup_in_webapp():
    """Test manual variant is found when DB variant is missing."""
    # This test will verify the integration
    pass
```

## Files to Create/Modify

**New Files:**
- `tools/variants_manager.py` - Generalized variant manager (refactored from gui2)
- `tests/test_variants_manager.py` - Unit tests for VariantManager
- `exporter/webapp/templates/manual_variant.html` - Template for manual variants
- `exporter/webapp/templates/manual_variant_summary.html` - Summary template

**Modified Files:**
- `gui2/variants.py` - Update to import from `tools.variants_manager`
- `exporter/webapp/toolkit.py` - Add manual variant check
- `exporter/webapp/data_classes.py` - Add ManualVariantData class
- `conductor/tracks/<track_id>/metadata.json` - Track metadata (auto)
- `conductor/tracks/<track_id>/spec.md` - Specification (auto)
- `conductor/tracks/<track_id>/plan.md` - This plan (auto)

## Notes
- Webapp already handles niggahita conversion (ṃ ↔ ṁ) in line 44 of toolkit.py
- Manual variants use simple "variant reading of {main}" format (GoldenDict style)
- Both DB variants and manual variants should be shown when both exist
- The `VariantManager` should be instantiated once and cached for performance
