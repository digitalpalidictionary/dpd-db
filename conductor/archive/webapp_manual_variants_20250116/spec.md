# Webapp: Include Manual Variants from variant_readings.tsv

## Overview
The webapp is missing variant readings that GoldenDict correctly includes. This is because:
- **GoldenDict** has TWO separate dictionaries:
  - `exporter/variants/variants_exporter.py` - Auto-harvested DB variants
  - `exporter/goldendict/export_variant_spelling.py` - Manual TSV variants
- **Webapp** only queries the `lookup.variant` column (auto-harvested), missing manual TSV variants

## Problem Description
Manual variants collected in `variant_readings.tsv` (like `celaṇḍukena`, `pāṇamatimāpayato`, etc.) are:
- ✅ Available in GoldenDict (via `export_variant_spelling.py`)
- ❌ Missing in webapp (only searches database, not TSV file)

## Solution
Modify the webapp search to check `variant_readings.tsv` when no DB variants are found, similar to how `export_variant_spelling.py` works.

### Data Structures
| Type | Structure | Source |
|------|-----------|--------|
| **DB Variants** | `{corpus: {book: [[context, variant], ...]}}` | Auto-harvested from texts |
| **Manual Variants** | `{variant: main}` | `variant_readings.tsv` |

### Presentation
Show **two separate sections** in the webapp, styled like GoldenDict:
1. **DB Variants** - Full table with source, book, context, variant (existing template)
2. **Manual Variants** - Simple list: "variant reading of {main}" (new, using GoldenDict template)

## Functional Requirements
1. When a user searches for a word in the webapp
2. Check DB for variants (existing behavior)
3. Also check `variant_readings.tsv` for manual variants
4. Display BOTH types if both exist
5. Display manual variants using the simple format from GoldenDict

### Data Conversion
Convert TSV format to display format:
```python
# TSV: {variant: main}
# Display: "variant reading of <b><i>{main}</i></b>"
```

## Refactoring Requirement
The existing `gui2/variants.py` contains `VariantReadingFileManager` which should be generalized into `tools/variants_manager.py` for reuse by both GUI2 and webapp.

## Acceptance Criteria
- [ ] Searching for `celaṇḍukena` in webapp returns manual variant result
- [ ] Searching for `pāṇamatimāpayato` in webapp returns manual variant result  
- [ ] Both DB variants and manual variants are shown when both exist
- [ ] Manual variants use simple "variant reading of {main}" format
- [ ] All ~1223 manual variants from `variant_readings.tsv` are searchable
- [ ] `gui2/variants.py` is updated to use the generalized `tools/variants_manager.py`

## Out of Scope
- Loading manual variants into the database
- Changes to other exporters (TPR, TBW, etc.)
