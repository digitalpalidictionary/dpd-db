# Spec: Mako to Jinja2 Template Refactoring

## Overview

This track aims to modernize the Digital Pāḷi Dictionary (DPD) project by refactoring all legacy Mako templates to Jinja2 templates. This refactoring will improve maintainability, code readability, and alignment with modern Python web templating standards.

**CRITICAL SUCCESS CRITERION**: Jinja2 output must match Mako output **character-for-character, byte-for-byte**. Any deviation (including hidden whitespace or encoding) is considered a failure.

## Architectural Goals

To ensure long-term maintainability and alignment with the Webapp, this refactoring enforces a major architectural shift across all exporters:

1.  **Unified Data Model (ViewModel Pattern):**
    *   Exporters MUST use ViewModel classes that identically mirror the structure of `exporter/webapp/data_classes.py`.
    *   **HeadwordData:** Used for DPD headwords.
    *   **RootData:** Used for Roots dictionary.
    *   **DeconstructorData:** Used for Deconstructor.
    *   **VariantData / SpellingData / GrammarData:** Used for associated associated dictionaries.
    *   **Role:** These classes act as **ViewModels**. All complex logic (formatting, newlines, calculated fields, grammar line construction) MUST be performed in these Python classes *before* rendering. The template should contain minimal logic.
    *   **Constraint:** Newline replacement ("\n" to "<br>") must be handled within these data classes (using a Proxy object if necessary to avoid database writes), keeping the exporter logic clean and preventing database locks in multiprocessing.

2.  **Master Template Consolidation (GoldenDict):**
    *   The 14+ partial templates (`dpd_header.html`, `dpd_grammar.html`, etc.) used by the GoldenDict exporter MUST be consolidated into a single master `dpd_headword.html`.
    *   This reduces the overhead of multiple file reads and rendering calls during large export runs.
    *   Conditional logic moves from Python strings to Jinja2 control structures (`{% if ... %}`).

3.  **TPR Decoupling:**
    *   TPR MUST utilize its own dedicated `tpr_headword.html`.
    *   It MUST NOT depend on GoldenDict partials.
    *   It MUST eliminate post-processing regex hacks by generating the correct HTML structure directly in the template.

4.  **Binary Parity & Verification:**
    *   The final Jinja2 output must be a byte-for-byte match with the Mako baseline.
    *   Verification tools must account for encoding (UTF-8), line endings (LF), and whitespace.

## Scope of Migration

The following modules and their associated templates are in scope:

- **GoldenDict Exporter:**
    - `export_dpd.py` (Headwords)
    - `export_roots.py` (Roots)
    - `export_epd.py` (English-Pali Dictionary)
    - `export_help.py` (Help & Abbreviations)
    - `export_variant_spelling.py` (Variants & Spelling Mistakes)
- **Kindle Exporter:**
    - `kindle_exporter.py`
- **Deconstructor Exporter:**
    - `deconstructor_exporter.py`
- **Grammar Dict Exporter:**
    - `grammar_dict.py`
- **TPR Exporter:**
    - `tpr_exporter.py`

## Critical Constraints

### Safety Requirements

⚠️ **NEVER overwrite or edit existing exporter folders directly**
- ✅ ALWAYS duplicate entire exporter folders (e.g., `exporter/goldendict/` → `exporter/goldendict2/`)
- ✅ Work EXCLUSIVELY in the duplicated `*2/` folders.
- ✅ Keep both original and duplicated folders side-by-side during development.
- ✅ **NEVER** delete or rename the original folders until the final "Cleanup" phase is explicitly approved by the user.

### Output Matching Requirements

- ✅ **Golden Master Strategy:** Capture baseline outputs ("Golden Masters") from Mako templates BEFORE any conversion.
- ✅ **Binary Verification:** Comparison tools must use binary/hex comparison to detect encoding shifts (UTF-8 vs BOM) or hidden whitespace.
- ✅ **Shadow Testing:** Run the new Jinja2 exporters alongside the original Mako exporters during verification.

## Acceptance Criteria

- [ ] GoldenDict uses a single `dpd_headword.html` master template.
- [ ] GoldenDict `HeadwordData` acts as a ViewModel, matching Webapp structure.
- [ ] TPR uses a dedicated template with no regex post-processing.
- [ ] All exporters produce output identical to the Mako baseline (verified via binary diff).
- [ ] No `mako` imports remain in the codebase (final step).
