# Plan: Mako to Jinja2 Template Refactoring

## Phase 1: Discovery Phase

- [ ] Task: Identify all Python files using Mako rendering
  - [ ] Search for `mako` imports across the project
  - [ ] Search for `TemplateLookup` or similar Mako initialization patterns
  - [ ] List all Python files that render templates
- [ ] Task: Map template files to Python code
  - [ ] Trace template directory paths from Mako initialization
  - [ ] Identify all HTML files used as Mako templates
  - [ ] Create a mapping document listing: Python file → Template directory → Template files
- [ ] Task: Analyze Mako syntax usage
  - [ ] Catalog Mako-specific syntax patterns used (e.g., `<% %>` blocks, `${}` expressions, inheritance)
  - [ ] Identify custom Mako filters and functions
  - [ ] Document template inheritance structure if present
- [ ] Task: Document findings
  - [ ] Write comprehensive mapping document
  - [ ] Note any complex logic or edge cases
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
  - [ ] Document common syntax translations (loops, conditionals, variables)
  - [ ] Document filter translations
  - [ ] Document inheritance differences
- [ ] Task: Conductor - User Manual Verification 'Setup and Configuration' (Protocol in workflow.md)

## Phase 3: Refactor Core Exporter Templates

- [ ] Task: Refactor GoldenDict exporter templates
  - [ ] Write test: GoldenDict export data output matches original Mako output
  - [ ] Implement: Convert GoldenDict Mako templates to Jinja2
  - [ ] Implement: Update GoldenDict exporter Python code to use Jinja2
  - [ ] Verify: GoldenDict data output accuracy matches original
- [ ] Task: Refactor Webapp exporter templates
  - [ ] Write test: Webapp export data output matches original Mako output
  - [ ] Implement: Convert Webapp Mako templates to Jinja2
  - [ ] Implement: Update Webapp exporter Python code to use Jinja2
  - [ ] Verify: Webapp data output accuracy matches original
- [ ] Task: Refactor MDict exporter templates
  - [ ] Write test: MDict export data output matches original Mako output
  - [ ] Implement: Convert MDict Mako templates to Jinja2
  - [ ] Implement: Update MDict exporter Python code to use Jinja2
  - [ ] Verify: MDict data output accuracy matches original
- [ ] Task: Refactor Kindle exporter templates
  - [ ] Write test: Kindle export data output matches original Mako output
  - [ ] Implement: Convert Kindle Mako templates to Jinja2
  - [ ] Implement: Update Kindle exporter Python code to use Jinja2
  - [ ] Verify: Kindle data output accuracy matches original
- [ ] Task: Refactor Kobo exporter templates
  - [ ] Write test: Kobo export data output matches original Mako output
  - [ ] Implement: Convert Kobo Mako templates to Jinja2
  - [ ] Implement: Update Kobo exporter Python code to use Jinja2
  - [ ] Verify: Kobo data output accuracy matches original
- [ ] Task: Refactor PDF exporter templates
  - [ ] Write test: PDF export data output matches original Mako output
  - [ ] Implement: Convert PDF Mako templates to Jinja2
  - [ ] Implement: Update PDF exporter Python code to use Jinja2
  - [ ] Verify: PDF data output accuracy matches original
- [ ] Task: Refactor other exporter templates (TXT, TPR, TBW, etc.)
  - [ ] Write test: Other exports data output matches original Mako output
  - [ ] Implement: Convert remaining Mako templates to Jinja2
  - [ ] Implement: Update remaining exporter Python code to use Jinja2
  - [ ] Verify: Remaining data outputs accuracy match original
- [ ] Task: Conductor - User Manual Verification 'Refactor Core Exporter Templates' (Protocol in workflow.md)

## Phase 4: Remove Mako Dependencies

- [ ] Task: Remove Mako from project dependencies
  - [ ] Write test: No Mako imports remain in the codebase
  - [ ] Implement: Remove `mako` from project dependencies using `uv remove`
  - [ ] Verify: All code runs without Mako installed
- [ ] Task: Clean up Mako-related code artifacts
  - [ ] Write test: No Mako syntax remains in template files
  - [ ] Implement: Remove any Mako-specific utility functions
  - [ ] Verify: Codebase is fully migrated to Jinja2
- [ ] Task: Conductor - User Manual Verification 'Remove Mako Dependencies' (Protocol in workflow.md)

## Phase 5: Documentation Updates

- [ ] Task: Update exporter README files
  - [ ] Write test: README files reference Jinja2 instead of Mako
  - [ ] Implement: Update all exporter README files to reflect Jinja2 usage
  - [ ] Verify: Documentation is accurate and up-to-date
- [ ] Task: Update technical documentation
  - [ ] Write test: Technical docs reference Jinja2 instead of Mako
  - [ ] Implement: Update relevant technical documentation
  - [ ] Verify: Documentation is consistent
- [ ] Task: Update main README if needed
  - [ ] Write test: Main README accurately describes templating system
  - [ ] Implement: Update main README if it mentions Mako
  - [ ] Verify: Project documentation is coherent
- [ ] Task: Conductor - User Manual Verification 'Documentation Updates' (Protocol in workflow.md)

## Phase 6: Final Verification and Testing

- [ ] Task: Run full test suite
  - [ ] Implement: Execute `pytest`
  - [ ] Verify: All data output accuracy tests pass
- [ ] Task: Run linter and static analysis
  - [ ] Implement: Execute `ruff check` and `ruff format --check`
  - [ ] Verify: No linting errors or formatting issues
- [ ] Task: Manual verification of all exports
  - [ ] Implement: Generate sample exports for each format
  - [ ] Verify: Exports data matches expected output
- [ ] Task: Conductor - User Manual Verification 'Final Verification and Testing' (Protocol in workflow.md)
