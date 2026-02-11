# Spec: Mako to Jinja2 Template Refactoring

## Overview

This track aims to modernize the Digital Pāḷi Dictionary (DPD) project by refactoring all legacy Mako templates to Jinja2 templates. This refactoring will improve maintainability, code readability, and alignment with modern Python web templating standards.

**CRITICAL SUCCESS CRITERION**: Jinja2 output must match Mako output character-for-character (after minification). Any deviation is considered a failure.

## Motivation

- **Maintainability:** Mako templates are deprecated and more difficult to maintain
- **Readability:** Jinja2 templates produce HTML that is easier to read and work with
- **Modernization:** Align with modern Python web templating standards
- **Performance:** Jinja2 offers better performance and caching capabilities
- **Developer Experience:** Better documentation, tooling, and community support

## Previous Attempt and Lessons Learned

A previous attempt at this migration **FAILED** because:
1. Could not accurately match old Mako output with new Jinja2 output
2. No baseline capture before conversion
3. No systematic output comparison strategy
4. Whitespace handling differences between Mako and Jinja2
5. All templates converted at once instead of incrementally
6. Insufficient testing on diverse sample data

**This spec addresses all these issues.**

## Critical Constraints

### Safety Requirements

⚠️ **NEVER overwrite or edit existing exporter folders directly**
- ✅ ALWAYS duplicate entire exporter folders (e.g., `exporter/goldendict/` → `exporter/goldendict2/`)
- ✅ Work EXCLUSIVELY in the duplicated `*2/` folders
- ✅ Keep both original and duplicated folders side-by-side during development
- ✅ Only remove original folders after 100% verification and user approval
- ✅ ALWAYS work in a git branch with a worktree for parallel testing

### Output Matching Requirements

- ✅ Capture baseline outputs from Mako templates BEFORE any conversion
- ✅ Build output comparison utilities to verify character-by-character matching
- ✅ Test with large, diverse sample sets (100-1000+ entries depending on exporter)
- ✅ Both automated comparison and manual verification required
- ✅ Test in actual applications (GoldenDict, Kindle devices, etc.)
- ✅ If outputs don't match: fix and retest until they do

### Incremental Approach

- ✅ Convert exporters from simplest to most complex
- ✅ Proof of concept with simplest exporter first
- ✅ Validate each exporter completely before moving to next
- ✅ Document lessons learned after each conversion

## Scope

- **All Mako Modules:** Refactor Mako templates across the entire project, including:
  - All exporter directories (GoldenDict, MDict, Kindle, Kobo, PDF, TPR, Grammar Dict, Deconstructor, etc.)
  - Any other modules utilizing Mako templates
  - Corresponding Python code that renders these templates
  - Associated HTML files

- **Excluded from scope:**
  - Webapp exporter (already uses Jinja2 via FastAPI)
  - Kobo exporter (may already use Jinja2 - verify first)

## Functional Requirements

1. **Discovery Phase:**
   - Identify all Python files that utilize Mako rendering (search for `mako` imports and template initialization)
   - Trace template initialization to identify all HTML files used as Mako templates
   - Document the relationships between templates, Python code, and HTML output
   - Create a mapping of which HTML files are Mako templates vs. static HTML
   - **Capture baseline outputs:** Generate sample outputs from ALL exporters using current Mako templates
   - Store baseline outputs with clear naming and documentation

2. **Setup Phase:**
   - Add Jinja2 dependency to project
   - Create Jinja2 environment setup utility with proper whitespace handling
   - Build output comparison utilities for character-by-character verification
   - Create automated syntax conversion script for common patterns

3. **Conversion Phase:**
   - Duplicate entire exporter folders (e.g., `exporter/goldendict/` → `exporter/goldendict2/`)
   - Work exclusively in duplicated folders, never touching originals
   - Convert templates from simplest to most complex:
     1. Grammar Dict / Deconstructor (2-3 templates each)
     2. TPR (1-3 templates)
     3. GoldenDict - Variant/Spelling, EPD, Help (medium complexity)
     4. GoldenDict - Roots (6 templates)
     5. Kindle (8 templates, EPUB structure)
     6. GoldenDict - Main DPD (14 templates, multiprocessing, MOST COMPLEX)
     7. PDF, Kobo, and any remaining exporters
   - For each conversion:
     - Convert all Mako syntax to Jinja2 syntax in template files
     - Update Python code to use Jinja2 rendering engine
     - Ensure all template logic (loops, conditionals, filters, etc.) is correctly translated
     - **Maintain output matching:** Compare outputs character-by-character
     - Iterate until outputs match EXACTLY

4. **Verification Phase:**
   - All converted templates must render correctly
   - All exporters must produce **identical** output to the original Mako versions
   - No data loss or corruption in generated output
   - Test in actual applications (GoldenDict app, Kindle devices, etc.)
   - Performance must be within 10% of original Mako implementation

## Non-Functional Requirements

1. **Code Quality:**
    - Follow existing code style guidelines defined in `conductor/code_styleguides/`
    - Ensure type hints are properly maintained in updated Python code
    - No linting or static analysis errors

2. **Testing:**
    - Write tests to verify data output accuracy for each exporter
    - Compare Jinja2 output against original Mako output to ensure functional equivalence
    - Do not test UI components - user interaction will reveal UI issues
    - Do not test internal function implementation details - focus on data output accuracy
    - Test with large, diverse sample sets (100-1000+ entries depending on exporter)
    - Both automated and manual verification required

3. **Documentation:**
    - Update any relevant README.md files to reflect the new templating system
    - Update technical documentation if needed

4. **Dependencies:**
    - Keep Mako installed throughout the entire conversion process for comparison purposes
    - Only remove Mako dependency as the FINAL step after merge to main and verification

## Acceptance Criteria

- [ ] All Python files using Mako have been identified and updated to use Jinja2
- [ ] All template files containing Mako syntax have been converted to Jinja2
- [ ] All exporters produce functionally identical output to the original Mako versions
- [ ] Data output accuracy tests pass for each exporter
- [ ] No linting or static analysis errors
- [ ] Relevant documentation (README files) have been updated
- [ ] Manual verification confirms all dictionary exports work correctly

## Out of Scope

- Creating new exporters beyond existing functionality
- Modifying the data models or database schema
- Changes to the core database logic
- Performance optimizations beyond the natural benefits of Jinja2

## Real Issues to Address

1. **Syntax Translation Complexity:** The conversion from Mako `${var}` and `% if condition:` to Jinja2 `{{var}}` and `{% if condition %}` requires careful handling.

2. **Template Logic Consistency:** Ensuring all conditional logic, loops, and expressions work identically after conversion.

3. **Testing and Verification:** Making sure the output remains functionally identical after conversion with proper test coverage.

## Assumptions Validated

- The multiprocessing architecture in `goldendict/export_dpd.py` does NOT have serialization issues, as templates are created locally in each child process rather than being passed between processes.
