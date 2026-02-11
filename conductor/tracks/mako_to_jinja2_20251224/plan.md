# Plan: Mako to Jinja2 Template Refactoring

## CRITICAL REQUIREMENTS

⚠️ **NEVER overwrite or edit existing folders/files directly**  
✅ **ALWAYS work in duplicated folders (e.g., `templates2`, `templates_jinja2`)**  
✅ **ALWAYS work in a git branch with a worktree**  
✅ **OUTPUT MATCHING IS MANDATORY**: New Jinja2 output must match Mako output character-for-character (after minification)

## Phase 0: Project Safety Setup

- [~] Task: Create git branch and worktree
  - [ ] Create branch: `refactor/mako-to-jinja2-v2`
  - [ ] Create worktree in separate directory for easy parallel testing
  - [ ] Document worktree path and usage instructions
- [ ] Task: Establish folder duplication strategy
  - [ ] Document naming convention: Duplicate ENTIRE exporter folders
  - [ ] Example: `exporter/goldendict/` → `exporter/goldendict2/`
  - [ ] Example: `exporter/kindle/` → `exporter/kindle2/`
  - [ ] Example: `exporter/grammar_dict/` → `exporter/grammar_dict2/`
  - [ ] **NEVER modify original exporter folders** - they remain completely untouched
  - [ ] Work exclusively in the `*2/` folders
  - [ ] Keep both original and duplicated folders side-by-side during development
  - [ ] Only remove original folders after 100% verification and user approval
- [ ] Task: Conductor - User Manual Verification 'Project Safety Setup' (Protocol in workflow.md)

## Phase 1: Discovery and Baseline Capture

- [ ] Task: Identify all Python files using Mako rendering (ALREADY DONE - see discovery_report.md)
  - [ ] Search for `mako` imports across the project
  - [ ] Search for `TemplateLookup` or similar Mako initialization patterns
  - [ ] List all Python files that render templates
- [ ] Task: Map template files to Python code (ALREADY DONE - see discovery_report.md)
  - [ ] Trace template directory paths from Mako initialization
  - [ ] Identify all HTML files used as Mako templates
  - [ ] Create a mapping document listing: Python file → Template directory → Template files
- [ ] Task: Analyze Mako syntax usage (ALREADY DONE - see syntax_conversion_guide.md)
  - [ ] Catalog Mako-specific syntax patterns used (e.g., `${}` expressions, `% if` conditionals)
  - [ ] Identify complex template logic that may require manual conversion
  - [ ] Document template inheritance structure if present
- [ ] Task: Capture Mako baseline outputs
  - [ ] Write script to generate sample outputs from EACH exporter using current Mako templates
  - [ ] Save outputs to `baseline_outputs/` directory with clear naming
  - [ ] Include at least 10 diverse samples per exporter (simple, complex, edge cases)
  - [ ] Store raw (pre-minified) and minified versions separately
  - [ ] Document which database records were used for each baseline
- [ ] Task: Document findings
  - [ ] Write comprehensive mapping document
  - [ ] Note any complex logic or edge cases that need special attention
- [ ] Task: Conductor - User Manual Verification 'Discovery Phase' (Protocol in workflow.md)

## Phase 2: Setup and Configuration

- [ ] Task: Add Jinja2 dependency
  - [ ] Write test: Verify Jinja2 can be imported
  - [ ] Implement: Add `jinja2` to project dependencies using `uv add`
  - [ ] Verify: Jinja2 is available in the environment
- [ ] Task: Create Jinja2 environment setup utility
  - [ ] Write test: Jinja2 environment can be initialized with correct loader
  - [ ] Implement: Create reusable Jinja2 setup function/module in `exporter/jinja2_env.py`
  - [ ] Verify: Environment is configured correctly (auto-escaping, filters, etc.)
  - [ ] Ensure Jinja2 whitespace handling matches Mako (use `trim_blocks=True, lstrip_blocks=True`)
- [ ] Task: Write Mako to Jinja2 syntax conversion guide (ALREADY DONE - see syntax_conversion_guide.md)
  - [ ] Document common syntax translations (variables: `${}` → `{{}}`)
  - [ ] Document control structures translations (`% if` → `{% if %}`, etc.)
  - [ ] Document any special cases or limitations
- [ ] Task: Create output comparison utilities
  - [ ] Write test: Comparison utility can detect HTML differences accurately
  - [ ] Implement: `compare_template_outputs.py` script
  - [ ] Features: Normalize whitespace, compare minified vs raw, highlight differences
  - [ ] Implement: Automatic diffing with colored output for human review
  - [ ] Implement: Option to save comparison reports to file
- [ ] Task: Conductor - User Manual Verification 'Setup and Configuration' (Protocol in workflow.md)

## Phase 3: Conversion Tools and Proof of Concept

- [ ] Task: Create automated syntax conversion script
  - [ ] Write test: Script correctly converts basic Mako syntax to Jinja2
  - [ ] Implement: Automated converter for common patterns (`${}` → `{{}}`, `% if` → `{% if %}`, etc.)
  - [ ] Verify: Script handles edge cases appropriately
  - [ ] Add option to convert in-place or to new directory
- [ ] Task: Proof of Concept - Convert simplest exporter first
  - [ ] Identify simplest exporter (e.g., `deconstructor` or `grammar_dict`)
  - [ ] Duplicate ENTIRE folder: `exporter/grammar_dict/` → `exporter/grammar_dict2/`
  - [ ] Work exclusively in `grammar_dict2/` folder
  - [ ] Convert templates to Jinja2 in `grammar_dict2/templates/`
  - [ ] Update Python code in `grammar_dict2/` to use Jinja2
  - [ ] Generate outputs with both original (Mako) and grammar_dict2 (Jinja2)
  - [ ] Compare outputs character-by-character (using comparison utility)
  - [ ] Iterate until outputs match EXACTLY
  - [ ] Document lessons learned and edge cases discovered
- [ ] Task: Prepare template validation utilities
  - [ ] Write test: Validation utilities can compare Mako and Jinja2 output
  - [ ] Implement: Utilities to validate template functionality after conversion
  - [ ] Verify: Validation tools work correctly with both template engines
- [ ] Task: Conductor - User Manual Verification 'Conversion Tools and POC' (Protocol in workflow.md)

## Phase 4: Incremental Template Conversion (Ordered by Complexity)

**Strategy**: Convert exporters from simplest to most complex, validating each completely before moving to the next.
**Approach**: Duplicate ENTIRE exporter folder (e.g., `exporter/goldendict/` → `exporter/goldendict2/`), work in the `*2/` folder.

### 4.1: Grammar Dict and Deconstructor (Simplest - 2-3 templates each)

- [ ] Task: Convert Grammar Dict exporter
  - [ ] Duplicate folder: `exporter/grammar_dict/` → `exporter/grammar_dict2/`
  - [ ] Convert templates to Jinja2 in `grammar_dict2/templates/`
  - [ ] Update `grammar_dict2/grammar_dict.py` to use Jinja2
  - [ ] Write test: Compare Grammar Dict Mako vs Jinja2 output for 20+ samples
  - [ ] Implement: Run comparison on diverse sample data
  - [ ] Verify: Outputs match character-for-character (minified)
  - [ ] Fix any discrepancies and re-test until perfect match
- [ ] Task: Convert Deconstructor exporter
  - [ ] Duplicate folder: `exporter/deconstructor/` → `exporter/deconstructor2/`
  - [ ] Convert templates to Jinja2 in `deconstructor2/templates/`
  - [ ] Update `deconstructor2/deconstructor_exporter.py` to use Jinja2
  - [ ] Write test: Compare Deconstructor Mako vs Jinja2 output for 20+ samples
  - [ ] Verify: Outputs match character-for-character (minified)

### 4.2: TPR (Medium - 1-3 templates)

- [ ] Task: Convert TPR exporter
  - [ ] Duplicate folder: `exporter/tpr/` → `exporter/tpr2/`
  - [ ] Convert templates to Jinja2 in `tpr2/templates/`
  - [ ] Update `tpr2/tpr_exporter.py` to use Jinja2
  - [ ] Write test: Compare TPR output (50+ samples)
  - [ ] Verify: Perfect output match

### 4.3: GoldenDict - Variant/Spelling, EPD, Help (Medium - separate from main DPD)

- [ ] Task: Convert GoldenDict export scripts (non-DPD)
  - [ ] Duplicate folder: `exporter/goldendict/` → `exporter/goldendict2/`
  - [ ] Convert variant and spelling templates in `goldendict2/templates/`
  - [ ] Update `goldendict2/export_variant_spelling.py` to use Jinja2
  - [ ] Write test: Compare outputs (30+ samples each type)
  - [ ] Convert EPD template in `goldendict2/templates/`
  - [ ] Update `goldendict2/export_epd.py` to use Jinja2
  - [ ] Write test: Compare EPD outputs (100+ samples - heavily used)
  - [ ] Convert help templates in `goldendict2/templates/`
  - [ ] Update `goldendict2/export_help.py` to use Jinja2
  - [ ] Write test: Compare help outputs (all help topics)
  - [ ] Verify: Perfect output match for all three

### 4.4: GoldenDict - Roots Dictionary (Medium-High - 6 templates)

- [ ] Task: Convert Roots templates (in goldendict2)
  - [ ] Convert all 6 root templates to Jinja2 in `goldendict2/templates/`
  - [ ] Update `goldendict2/export_roots.py` to use Jinja2
  - [ ] Write test: Compare root outputs (100+ samples covering all root types)
  - [ ] Verify: Perfect output match

### 4.5: Kindle Exporter (High - 8 templates, complex EPUB structure)

- [ ] Task: Convert Kindle exporter
  - [ ] Duplicate folder: `exporter/kindle/` → `exporter/kindle2/`
  - [ ] Convert all 8 Kindle templates to Jinja2 in `kindle2/templates/`
  - [ ] Update `kindle2/kindle_exporter.py` to use Jinja2
  - [ ] Write test: Compare Kindle EPUB outputs (50+ entries, validate EPUB structure)
  - [ ] Verify: Perfect output match AND valid EPUB files
  - [ ] Manual verification: Test EPUB on actual Kindle device

### 4.6: GoldenDict Main DPD (MOST COMPLEX - 14 templates, multiprocessing)

- [ ] Task: Convert DPD Header template (in goldendict2)
  - [ ] Convert dpd_header.html in `goldendict2/templates/`
  - [ ] Test header rendering separately before full integration
- [ ] Task: Convert DPD Definition and Grammar templates
  - [ ] Convert dpd_definition.html in `goldendict2/templates/`
  - [ ] Convert dpd_grammar.html (complex conditionals)
  - [ ] Test these templates with diverse POS (noun, verb, indeclinable, etc.)
- [ ] Task: Convert DPD Example and Sutta Info templates
  - [ ] Convert dpd_example.html in `goldendict2/templates/`
  - [ ] Convert dpd_sutta_info.html (large, complex template)
  - [ ] Test with entries that have many examples and sutta references
- [ ] Task: Convert Family templates
  - [ ] Convert dpd_family_root.html in `goldendict2/templates/`
  - [ ] Convert dpd_family_word.html
  - [ ] Convert dpd_family_compound.html
  - [ ] Convert dpd_family_idiom.html
  - [ ] Convert dpd_family_set.html
  - [ ] Test with entries that have extensive family connections
- [ ] Task: Convert remaining DPD templates
  - [ ] Convert dpd_inflection.html in `goldendict2/templates/`
  - [ ] Convert dpd_frequency.html
  - [ ] Convert dpd_feedback.html
  - [ ] Convert button_box template
- [ ] Task: Integration and full DPD testing
  - [ ] Update `goldendict2/export_dpd.py` to use Jinja2 templates
  - [ ] Ensure multiprocessing compatibility (templates created in each process)
  - [ ] Write test: Compare DPD outputs (500+ entries covering all POS types, edge cases)
  - [ ] Test specific edge cases: long definitions, complex compounds, multiple families
  - [ ] Verify: Perfect output match for ALL samples
  - [ ] Performance test: Ensure rendering speed is acceptable

### 4.7: PDF, Kobo, and other exporters

- [ ] Task: Convert PDF exporter (if using Mako)
  - [ ] Duplicate folder: `exporter/pdf/` → `exporter/pdf2/`
  - [ ] Assess current template engine
  - [ ] Convert templates if needed
  - [ ] Test PDF generation
- [ ] Task: Convert Kobo exporter (if using Mako)
  - [ ] Duplicate folder: `exporter/kobo/` → `exporter/kobo2/`
  - [ ] Note: Kobo may already use Jinja2 - verify this
  - [ ] Convert if needed
- [ ] Task: Review and convert any remaining exporters
  - [ ] Audit all exporters for Mako usage
  - [ ] Duplicate and convert any remaining exporters
  - [ ] Test each thoroughly

- [ ] Task: Conductor - User Manual Verification 'Template Conversion' (Protocol in workflow.md)

## Phase 5: Comprehensive Testing and Final Verification

- [ ] Task: Final side-by-side output comparison
  - [ ] Write test: Automated comparison of Mako vs Jinja2 for EVERY exporter
  - [ ] Run comparison on large sample sets (1000+ entries for main DPD)
  - [ ] Generate detailed comparison report showing any remaining differences
  - [ ] Verify: ALL outputs match character-for-character (minified)
  - [ ] If differences exist: identify root cause, fix, and retest
- [ ] Task: Real-world testing in actual dictionary apps
  - [ ] Generate full GoldenDict dictionary using Jinja2 templates
  - [ ] Install and test in GoldenDict application
  - [ ] Verify: All features work (buttons, popups, family connections, etc.)
  - [ ] Generate Kindle EPUB and test on actual Kindle device
  - [ ] Verify: Navigation, rendering, search all work correctly
- [ ] Task: Manual verification of complex cases
  - [ ] Test entries with maximum complexity (long definitions, many families, etc.)
  - [ ] Test entries with special characters, Unicode, Pāḷi diacritics
  - [ ] Test edge cases: empty fields, very long fields, special formatting
  - [ ] Verify: All render correctly
- [ ] Task: Performance comparison
  - [ ] Write test: Measure performance of Jinja2 vs Mako implementation
  - [ ] Implement: Run performance benchmarks for each exporter
  - [ ] Verify: Performance is acceptable or improved (target: within 10% of Mako)
- [ ] Task: Regression testing with full test suite
  - [ ] Implement: Run `pytest` on all existing tests
  - [ ] Verify: All tests still pass
  - [ ] Fix any broken tests (update test expectations if needed)
- [ ] Task: Conductor - User Manual Verification 'Testing and Verification' (Protocol in workflow.md)

## Phase 6: Cleanup and Migration (ONLY AFTER 100% VERIFICATION)

⚠️ **CRITICAL**: Do NOT perform cleanup until Phase 5 is 100% complete and verified by user

- [ ] Task: Rename folders and remove Mako exporters
  - [ ] For each exporter: Rename `exporter/name2/` → `exporter/name/` (removing old folder first)
  - [ ] Keep backup of original exporters in archive temporarily
  - [ ] Verify: Code still works after folder rename
- [ ] Task: Remove Mako-specific code from Python files
  - [ ] Remove Mako imports
  - [ ] Remove Mako Template initialization
  - [ ] Remove any Mako-specific utility functions
  - [ ] Update any configuration that references Mako
- [ ] Task: Clean up backup and temporary files
  - [ ] Remove baseline output directories (after archiving if needed)
  - [ ] Remove archived original exporter folders
  - [ ] Remove any temporary conversion scripts or utilities
  - [ ] Verify: Codebase is clean
- [ ] Task: Update documentation
  - [ ] Write test: README files reference Jinja2 instead of Mako
  - [ ] Implement: Update all relevant documentation to reflect Jinja2 usage
  - [ ] Update code comments that mention Mako
  - [ ] Update developer setup instructions if needed
  - [ ] Verify: Documentation is accurate and up-to-date
- [ ] Task: Conductor - User Manual Verification 'Cleanup and Documentation' (Protocol in workflow.md)

## Phase 7: Final Validation and Deployment

- [ ] Task: Run full test suite
  - [ ] Implement: Execute `pytest` with full coverage
  - [ ] Verify: All data output accuracy tests pass
  - [ ] Fix any remaining test failures
- [ ] Task: Run linter and static analysis
  - [ ] Implement: Execute `ruff check` and `ruff format --check`
  - [ ] Verify: No linting errors or formatting issues
  - [ ] Fix any issues found
- [ ] Task: End-to-end integration testing
  - [ ] Implement: Full export process for each exporter type
  - [ ] Test: Generate complete dictionaries for GoldenDict, Kindle, etc.
  - [ ] Verify: All exporters work correctly in production-like environment
  - [ ] Test in actual applications (GoldenDict, Kindle app, etc.)
- [ ] Task: Create rollback plan
  - [ ] Document: How to revert to Mako if critical issues are discovered
  - [ ] Keep Mako backup branch available
  - [ ] Document: Emergency rollback procedure
- [ ] Task: Merge to main
  - [ ] Create pull request from branch to main
  - [ ] Include comprehensive description of changes
  - [ ] Include test results and comparison reports
  - [ ] User review and approval
  - [ ] Merge to main only after user approval
- [ ] Task: Remove Mako from project dependencies (FINAL STEP)
  - [ ] Write test: No Mako imports remain in the codebase
  - [ ] Implement: Remove `mako` from project dependencies using `uv remove mako`
  - [ ] Verify: All code runs without Mako installed
  - [ ] This should be done AFTER merge to main and final verification
- [ ] Task: Conductor - User Manual Verification 'Final Validation' (Protocol in workflow.md)

---

## Notes on Previous Attempt and Lessons Learned

**Previous Failure Reason**: Could not accurately match old output with new output.

**Root Causes Identified**:
1. No baseline capture before conversion
2. No systematic output comparison strategy
3. Whitespace handling differences between Mako and Jinja2
4. Minification applied at different stages
5. Converted all templates at once instead of incrementally
6. Insufficient testing on diverse sample data

**Solutions Implemented in This Plan**:
1. ✅ Phase 0: Baseline output capture
2. ✅ Phase 2: Output comparison utilities
3. ✅ Phase 3: Proof of concept with simplest exporter first
4. ✅ Phase 4: Incremental conversion, ordered by complexity
5. ✅ Each conversion includes output matching requirement before proceeding
6. ✅ Large sample sets for testing (100-1000+ entries depending on exporter)
7. ✅ Both automated and manual verification
8. ✅ Real-world testing in actual dictionary applications
9. ✅ Never overwrite original templates - always work in parallel
10. ✅ Git branch with worktree for easy parallel testing
