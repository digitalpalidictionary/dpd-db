# Implementation Plan: Mac Dictionary Build Integration

## Phase 1: Research and Setup
- [x] Task: Research Apple Dictionary Development Kit requirements and XML schema
  - [x] Sub-task: Study MyDictionary.xml format and d:entry/d:index structure
  - [x] Sub-task: Review Dictionary Development Kit build process and dependencies
  - [x] Sub-task: Identify required Info.plist keys for DPD metadata
- [x] Task: Examine existing exporter structure for integration patterns
  - [x] Sub-task: Review exporter/kobo/ as reference for styling and templates
  - [x] Sub-task: Identify database query patterns for dictionary entries
- [x] Task: Create exporter/apple_dictionary/ module structure
  - [x] Sub-task: Create directory and __init__.py
  - [x] Sub-task: Set up module imports and dependencies
  - [x] Sub-task: Create README.md with documentation
  - [x] Sub-task: Create templates/dictionary.css with DPD branding
  - [x] Sub-task: Create templates/entry.html with Jinja2 template
  - [x] Sub-task: Implement apple_dictionary.py main export script
- [~] Task: Conductor - User Manual Verification 'Research and Setup' (Protocol in workflow.md)

## Phase 2: Python Export Script Implementation (TDD)
- [x] Task: Write tests for dictionary source generation
  - [x] Sub-task: Create test_apple_dictionary_export.py with 22 test cases
  - [x] Sub-task: Write test for XML entry generation with valid structure
  - [x] Sub-task: Write test for index value extraction from database
  - [x] Sub-task: Write test for inflection indices (multiple d:index per entry)
  - [x] Sub-task: Write test for CSS file generation
  - [x] Sub-task: Write test for plist file generation
  - [x] Sub-task: Run tests and confirm they fail (Red Phase)
- [x] Task: Implement apple_dictionary.py
  - [x] Sub-task: Implement database query for headwords and definitions
  - [x] Sub-task: Generate Dictionary.xml with proper Apple namespace
  - [x] Sub-task: Generate Dictionary.css with DPD branding
  - [x] Sub-task: Generate Info.plist with DPD metadata
  - [x] Sub-task: Support inflection indices (all forms searchable)
  - [x] Sub-task: Run tests and confirm they pass (Green Phase - 22/22 passing)
- [x] Task: Code quality and documentation
  - [x] Sub-task: Run uv run ruff check --fix and uv run ruff format
  - [x] Sub-task: Add module docstrings and function documentation
  - [x] Sub-task: Update exporter/apple_dictionary/README.md
- [~] Task: Conductor - User Manual Verification 'Python Export Script Implementation' (Protocol in workflow.md)

## Phase 3: GitHub Actions Workflow Integration
- [x] Task: Modify .github/workflows/draft_release.yml
  - [x] Sub-task: Rename existing job to 'build-linux' with outputs
  - [x] Sub-task: Add Apple Dictionary export step to build-linux job
    - [x] Export source files to exporter/share/apple_dictionary/
    - [x] Upload source files as artifacts (Dictionary.xml, Dictionary.css, Info.plist)
  - [x] Sub-task: Create 'build-macos' job (depends on build-linux)
    - [x] Download Apple Dictionary source artifacts
    - [x] Clone Dictionary Development Kit
    - [x] Compile .dictionary bundle using make
    - [x] Upload .dictionary as artifact
  - [x] Sub-task: Create 'create-release' job (depends on build-linux and build-macos)
    - [x] Download all artifacts from both jobs
    - [x] Create draft release with all assets including Digital-Pali-Dictionary.dictionary.zip
- [x] Task: Delete separate .github/workflows/build-mac-dictionary.yml
- [x] Task: Test workflow syntax and validation
  - [x] Sub-task: Validate YAML syntax (passed)
  - [x] Sub-task: All jobs properly configured with dependencies
- [~] Task: Conductor - User Manual Verification 'GitHub Actions Workflow' (Protocol in workflow.md)

## Phase 4: Integration and Testing
- [ ] Task: Integration testing
  - [ ] Sub-task: Test export script with actual database
  - [ ] Sub-task: Verify generated XML validates against Apple schema
  - [ ] Sub-task: Manual test of .dictionary file in Dictionary.app
- [ ] Task: Documentation updates
  - [ ] Sub-task: Update docs/technical/ with workflow documentation
  - [ ] Sub-task: Add Mac dictionary installation instructions
  - [ ] Sub-task: Update main README if needed
- [ ] Task: Conductor - User Manual Verification 'Integration and Testing' (Protocol in workflow.md)

## Phase 5: Deployment and Validation
- [ ] Task: Create test release to validate full workflow
  - [ ] Sub-task: Monitor workflow execution
  - [ ] Sub-task: Verify .dictionary file is attached to release
  - [ ] Sub-task: Download and test .dictionary file on Mac
- [ ] Task: Final review and cleanup
  - [ ] Sub-task: Review all generated files
  - [ ] Sub-task: Ensure all quality gates pass
- [ ] Task: Conductor - User Manual Verification 'Deployment and Validation' (Protocol in workflow.md)
