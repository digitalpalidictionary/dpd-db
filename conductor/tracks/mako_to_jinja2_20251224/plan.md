# Plan: Mako to Jinja2 Template Refactoring

## Phase 1: Discovery and Analysis

- [ ] Task: Identify all Python files using Mako rendering
  - [ ] Search for `mako` imports across the project
  - [ ] Search for `TemplateLookup` or similar Mako initialization patterns
  - [ ] List all Python files that render templates
- [ ] Task: Map template files to Python code
  - [ ] Trace template directory paths from Mako initialization
  - [ ] Identify all HTML files used as Mako templates
  - [ ] Create a mapping document listing: Python file → Template directory → Template files
- [ ] Task: Analyze Mako syntax usage
  - [ ] Catalog Mako-specific syntax patterns used (e.g., `${}` expressions, `% if` conditionals)
  - [ ] Identify complex template logic that may require manual conversion
  - [ ] Document template inheritance structure if present
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
  - [ ] Implement: Create reusable Jinja2 setup function/module
  - [ ] Verify: Environment is configured correctly (auto-escaping, filters, etc.)
- [ ] Task: Write Mako to Jinja2 syntax conversion guide
  - [ ] Document common syntax translations (variables: `${}` → `{{}}`)
  - [ ] Document control structures translations (`% if` → `{% if %}`, etc.)
  - [ ] Document any special cases or limitations
- [ ] Task: Conductor - User Manual Verification 'Setup and Configuration' (Protocol in workflow.md)

## Phase 3: Conversion Tools and Utilities

- [ ] Task: Create automated syntax conversion script
  - [ ] Write test: Script correctly converts basic Mako syntax to Jinja2
  - [ ] Implement: Automated converter for common patterns (`${}` → `{{}}`, `% if` → `{% if %}`, etc.)
  - [ ] Verify: Script handles edge cases appropriately
- [ ] Task: Prepare template validation utilities
  - [ ] Write test: Validation utilities can compare Mako and Jinja2 output
  - [ ] Implement: Utilities to validate template functionality after conversion
  - [ ] Verify: Validation tools work correctly with both template engines
- [ ] Task: Conductor - User Manual Verification 'Conversion Tools and Utilities' (Protocol in workflow.md)

## Phase 4: Template Conversion

- [ ] Task: Convert GoldenDict exporter templates
  - [ ] Write test: GoldenDict export data output matches original Mako output
  - [ ] Implement: Convert GoldenDict Mako templates to Jinja2 using automation where possible
  - [ ] Implement: Update GoldenDict exporter Python code to use Jinja2
  - [ ] Verify: GoldenDict data output accuracy matches original
- [ ] Task: Convert Webapp exporter templates
  - [ ] Write test: Webapp export data output matches original Mako output
  - [ ] Implement: Convert Webapp Mako templates to Jinja2 using automation where possible
  - [ ] Implement: Update Webapp exporter Python code to use Jinja2
  - [ ] Verify: Webapp data output accuracy matches original
- [ ] Task: Convert MDict exporter templates
  - [ ] Write test: MDict export data output matches original Mako output
  - [ ] Implement: Convert MDict Mako templates to Jinja2 using automation where possible
  - [ ] Implement: Update MDict exporter Python code to use Jinja2
  - [ ] Verify: MDict data output accuracy matches original
- [ ] Task: Convert Kindle exporter templates
  - [ ] Write test: Kindle export data output matches original Mako output
  - [ ] Implement: Convert Kindle Mako templates to Jinja2 using automation where possible
  - [ ] Implement: Update Kindle exporter Python code to use Jinja2
  - [ ] Verify: Kindle data output accuracy matches original
- [ ] Task: Convert Kobo exporter templates
  - [ ] Write test: Kobo export data output matches original Mako output
  - [ ] Implement: Convert Kobo Mako templates to Jinja2 using automation where possible
  - [ ] Implement: Update Kobo exporter Python code to use Jinja2
  - [ ] Verify: Kobo data output accuracy matches original
- [ ] Task: Convert PDF exporter templates
  - [ ] Write test: PDF export data output matches original Mako output
  - [ ] Implement: Convert PDF Mako templates to Jinja2 using automation where possible
  - [ ] Implement: Update PDF exporter Python code to use Jinja2
  - [ ] Verify: PDF data output accuracy matches original
- [ ] Task: Convert other exporter templates (TXT, TPR, TBW, etc.)
  - [ ] Write test: Other exports data output matches original Mako output
  - [ ] Implement: Convert remaining Mako templates to Jinja2 using automation where possible
  - [ ] Implement: Update remaining exporter Python code to use Jinja2
  - [ ] Verify: Remaining data outputs accuracy match original
- [ ] Task: Conductor - User Manual Verification 'Template Conversion' (Protocol in workflow.md)

## Phase 5: Testing and Verification

- [ ] Task: Comprehensive output comparison testing
  - [ ] Write test: Automated comparison of Mako vs Jinja2 output for each exporter
  - [ ] Implement: Run comprehensive comparison tests across all exporters
  - [ ] Verify: All outputs are functionally equivalent
- [ ] Task: Manual verification of all exports
  - [ ] Implement: Generate sample exports for each format
  - [ ] Verify: Exports data matches expected output and functionality
- [ ] Task: Performance comparison
  - [ ] Write test: Measure performance of Jinja2 vs Mako implementation
  - [ ] Implement: Run performance benchmarks for each exporter
  - [ ] Verify: Performance is acceptable or improved
- [ ] Task: Conductor - User Manual Verification 'Testing and Verification' (Protocol in workflow.md)

## Phase 6: Cleanup and Documentation

- [ ] Task: Remove Mako from project dependencies
  - [ ] Write test: No Mako imports remain in the codebase
  - [ ] Implement: Remove `mako` from project dependencies using `uv remove`
  - [ ] Verify: All code runs without Mako installed
- [ ] Task: Clean up Mako-related code artifacts
  - [ ] Write test: No Mako syntax remains in template files
  - [ ] Implement: Remove any Mako-specific utility functions
  - [ ] Verify: Codebase is fully migrated to Jinja2
- [ ] Task: Update documentation
  - [ ] Write test: README files reference Jinja2 instead of Mako
  - [ ] Implement: Update all relevant documentation to reflect Jinja2 usage
  - [ ] Verify: Documentation is accurate and up-to-date
- [ ] Task: Conductor - User Manual Verification 'Cleanup and Documentation' (Protocol in workflow.md)

## Phase 7: Final Validation

- [ ] Task: Run full test suite
  - [ ] Implement: Execute `pytest`
  - [ ] Verify: All data output accuracy tests pass
- [ ] Task: Run linter and static analysis
  - [ ] Implement: Execute `ruff check` and `ruff format --check`
  - [ ] Verify: No linting errors or formatting issues
- [ ] Task: End-to-end integration testing
  - [ ] Implement: Full export process for each exporter type
  - [ ] Verify: All exporters work correctly in production-like environment
- [ ] Task: Conductor - User Manual Verification 'Final Validation' (Protocol in workflow.md)
