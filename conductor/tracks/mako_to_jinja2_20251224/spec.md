# Spec: Mako to Jinja2 Template Refactoring

## Overview

This track aims to modernize the Digital Pāḷi Dictionary (DPD) project by refactoring all legacy Mako templates to Jinja2 templates. This refactoring will improve maintainability, code readability, and alignment with modern Python web templating standards.

## Motivation

- **Maintainability:** Mako templates are deprecated and more difficult to maintain
- **Readability:** Jinja2 templates produce HTML that is easier to read and work with
- **Modernization:** Align with modern Python web templating standards
- **Performance:** Jinja2 offers better performance and caching capabilities
- **Developer Experience:** Better documentation, tooling, and community support

## Scope

- **All Mako Modules:** Refactor Mako templates across the entire project, including:
  - All exporter directories (GoldenDict, MDict, Kindle, Kobo, PDF, Webapp, etc.)
  - Any other modules utilizing Mako templates
  - Corresponding Python code that renders these templates
  - Associated HTML files

## Functional Requirements

1. **Discovery Phase:**
   - Identify all Python files that utilize Mako rendering (search for `mako` imports and template initialization)
   - Trace template initialization to identify all HTML files used as Mako templates
   - Document the relationships between templates, Python code, and HTML output
   - Create a mapping of which HTML files are Mako templates vs. static HTML

2. **Refactoring Phase:**
   - Convert all Mako syntax to Jinja2 syntax in identified template files
   - Update Python code to use Jinja2 rendering engine instead of Mako
   - Ensure all template logic (loops, conditionals, filters, etc.) is correctly translated
   - Maintain functional equivalence - output must match the original Mako templates

3. **Verification Phase:**
   - All converted templates must render correctly
   - All exporters must produce identical output to the original Mako versions
   - No data loss or corruption in generated output

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

3. **Documentation:**
    - Update any relevant README.md files to reflect the new templating system
    - Update technical documentation if needed

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
