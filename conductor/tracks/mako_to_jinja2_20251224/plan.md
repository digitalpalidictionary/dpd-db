# Plan: Mako to Jinja2 Template Refactoring

## Phase 1: Discovery and Analysis

- [x] Task: Identify all Python files using Mako rendering
  - [x] Search for `mako` imports across the project
  - [x] Search for `TemplateLookup` or similar Mako initialization patterns
  - [x] List all Python files that render templates
- [x] Task: Map template files to Python code
  - [x] Trace template directory paths from Mako initialization
  - [x] Identify all HTML files used as Mako templates
  - [x] Create a mapping document listing: Python file → Template directory → Template files
- [x] Task: Analyze Mako syntax usage
  - [x] Catalog Mako-specific syntax patterns used (e.g., `${}` expressions, `% if` conditionals)
  - [x] Identify complex template logic that may require manual conversion
  - [x] Document template inheritance structure if present
- [x] Task: Document findings
  - [x] Write comprehensive mapping document
  - [x] Note any complex logic or edge cases that need special attention
- [ ] Task: Conductor - User Manual Verification 'Discovery Phase' (Protocol in workflow.md)

## Phase 2: Setup and Configuration

- [x] Task: Add Jinja2 dependency
  - [x] Write test: Verify Jinja2 can be imported ([`tests/test_jinja2_setup.py`](../../../tests/test_jinja2_setup.py))
  - [x] Implement: Add `jinja2` to project dependencies using `uv add`
  - [x] Verify: Jinja2 is available in the environment
- [x] Task: Create Jinja2 environment setup utility
  - [x] Write test: Jinja2 environment can be initialized with correct loader ([`tests/test_jinja2_env.py`](../../../tests/test_jinja2_env.py))
  - [x] Implement: Create reusable Jinja2 setup function/module ([`exporter/jinja2_env.py`](../../../exporter/jinja2_env.py))
  - [x] Verify: Environment is configured correctly (auto-escaping, filters, etc.)
- [x] Task: Write Mako to Jinja2 syntax conversion guide
  - [x] Document common syntax translations (variables: `${}` → `{{}}`)
  - [x] Document control structures translations (`% if` → `{% if %}`, etc.)
  - [x] Document any special cases or limitations ([`syntax_conversion_guide.md`](syntax_conversion_guide.md))
- [ ] Task: Conductor - User Manual Verification 'Setup and Configuration' (Protocol in workflow.md)

## Phase 3: Conversion Tools and Utilities

- [x] Task: Create automated syntax conversion script
  - [x] Write test: Script correctly converts basic Mako syntax to Jinja2 ([`tests/test_convert_mako_to_jinja2.py`](../../../tests/test_convert_mako_to_jinja2.py))
  - [x] Implement: Automated converter for common patterns (`${}` → `{{}}`, `% if` → `{% if %}`, etc.) ([`exporter/convert_mako_to_jinja2.py`](../../../exporter/convert_mako_to_jinja2.py))
  - [x] Verify: Script handles edge cases appropriately
- [x] Task: Prepare template validation utilities
  - [x] Write test: Validation utilities can compare Mako and Jinja2 output ([`tests/test_template_validator.py`](../../../tests/test_template_validator.py))
  - [x] Implement: Utilities to validate template functionality after conversion ([`exporter/template_validator.py`](../../../exporter/template_validator.py))
  - [x] Verify: Validation tools work correctly with both template engines
- [ ] Task: Conductor - User Manual Verification 'Conversion Tools and Utilities' (Protocol in workflow.md)

## Phase 4: Template Conversion

- [x] Task: Convert GoldenDict exporter templates
  - [x] Write test: GoldenDict export data output matches original Mako output
  - [x] Implement: Convert GoldenDict Mako templates to Jinja2 using automation where possible
  - [x] Implement: Update GoldenDict exporter Python code to use Jinja2
  - [x] Verify: GoldenDict data output accuracy matches original
- [x] Task: Convert Webapp exporter templates
  - [x] Write test: Webapp export data output matches original Mako output
  - [x] Implement: Convert Webapp Mako templates to Jinja2 using automation where possible
  - [x] Implement: Update Webapp exporter Python code to use Jinja2
  - [x] Verify: Webapp data output accuracy matches original
- [x] Task: Convert MDict exporter templates
  - [x] Write test: MDict export data output matches original Mako output
  - [x] Implement: Convert MDict Mako templates to Jinja2 using automation where possible
  - [x] Implement: Update MDict exporter Python code to use Jinja2
  - [x] Verify: MDict data output accuracy matches original
- [x] Task: Convert Kindle exporter templates
  - [x] Write test: Kindle export data output matches original Mako output
  - [x] Implement: Convert Kindle Mako templates to Jinja2 using automation where possible
  - [x] Implement: Update Kindle exporter Python code to use Jinja2
  - [x] Verify: Kindle data output accuracy matches original
- [x] Task: Convert Kobo exporter templates
  - [x] Write test: Kobo export data output matches original Mako output
  - [x] Implement: Convert Kobo Mako templates to Jinja2 using automation where possible
  - [x] Implement: Update Kobo exporter Python code to use Jinja2
  - [x] Verify: Kobo data output accuracy matches original
- [x] Task: Convert PDF exporter templates
  - [x] Write test: PDF export data output matches original Mako output
  - [x] Implement: Convert PDF Mako templates to Jinja2 using automation where possible
  - [x] Implement: Update PDF exporter Python code to use Jinja2
  - [x] Verify: PDF data output accuracy matches original
- [x] Task: Convert other exporter templates (TXT, TPR, TBW, etc.)
  - [x] Write test: Other exports data output matches original Mako output
  - [x] Implement: Convert remaining Mako templates to Jinja2 using automation where possible
  - [x] Implement: Update remaining exporter Python code to use Jinja2
  - [x] Verify: Remaining data outputs accuracy match original
- [x] Task: Conductor - User Manual Verification 'Template Conversion' (Protocol in workflow.md)

## Phase 5: Testing and Verification

- [x] Task: Comprehensive output comparison testing
  - [x] Write test: Automated comparison of Mako vs Jinja2 output for each exporter
  - [x] Implement: Run comprehensive comparison tests across all exporters
  - [x] Verify: All outputs are functionally equivalent
- [x] Task: Manual verification of all exports
  - [x] Implement: Generate sample exports for each format
  - [x] Verify: Exports data matches expected output and functionality
- [x] Task: Performance comparison
  - [x] Write test: Measure performance of Jinja2 vs Mako implementation
  - [x] Implement: Run performance benchmarks for each exporter
  - [x] Verify: Performance is acceptable or improved
- [x] Task: Conductor - User Manual Verification 'Testing and Verification' (Protocol in workflow.md)

## Phase 6: Cleanup and Documentation

- [x] Task: Remove Mako from project dependencies
  - [x] Write test: No Mako imports remain in the codebase
  - [x] Implement: Remove `mako` from project dependencies using `uv remove`
  - [x] Verify: All code runs without Mako installed
- [x] Task: Clean up Mako-related code artifacts
  - [x] Write test: No Mako syntax remains in template files
  - [x] Implement: Remove any Mako-specific utility functions
  - [x] Verify: Codebase is fully migrated to Jinja2
- [x] Task: Update documentation
  - [x] Write test: README files reference Jinja2 instead of Mako
  - [x] Implement: Update all relevant documentation to reflect Jinja2 usage
  - [x] Verify: Documentation is accurate and up-to-date
- [ ] Task: Conductor - User Manual Verification 'Cleanup and Documentation' (Protocol in workflow.md)

## Phase 7: Final Validation

- [x] Task: Run full test suite
  - [x] Implement: Execute `pytest`
  - [x] Verify: All data output accuracy tests pass
- [x] Task: Run linter and static analysis
  - [x] Implement: Execute `ruff check` and `ruff format --check`
  - [x] Verify: No linting errors or formatting issues
- [x] Task: End-to-end integration testing
  - [x] Implement: Full export process for each exporter type
  - [x] Verify: All exporters work correctly in production-like environment
- [ ] Task: Conductor - User Manual Verification 'Final Validation' (Protocol in workflow.md)
