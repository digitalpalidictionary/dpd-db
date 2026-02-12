# Plan: Mako to Jinja2 Template Refactoring

## CRITICAL REQUIREMENTS

⚠️ **NEVER overwrite or edit existing folders/files directly.**  
✅ **ALWAYS work in duplicated folders (e.g., `exporter/goldendict2/`).**  
✅ **OUTPUT MATCHING IS MANDATORY (Binary/Hex Check).**  
✅ **WEBAPP ALIGNMENT:** GoldenDict must use `HeadwordData` (ViewModel) and a Master Template.

## Phase 1: Discovery and Baseline Capture ("Golden Masters")
- [x] **Task: Baseline Capture**
  - [x] Create `capture_baselines.py`.
  - [x] Generate HTML samples for ALL exporters (GoldenDict, TPR, Kindle, etc.) using the *current* Mako code.
  - [x] Store in `baseline_outputs/` (treat these as immutable Golden Masters).

## Phase 2: Setup
- [x] **Task: Jinja2 Environment**
  - [x] Create `exporter/jinja2_env.py` with `trim_blocks=True`, `lstrip_blocks=True`.
- [x] **Task: Naming Convention**
  - [x] Use `.jinja` extension for all new templates to enable VS Code syntax highlighting (via "Better Jinja" extension) and distinguish from Mako `.html` templates.
- [x] **Task: Advanced Comparison Tools**
  - [x] Create `verify_output.py`.
  - [x] **Requirement:** Implement binary diffing (check for BOM, CRLF) to ensure byte-perfect matching.
  - [x] Support "Shadow Testing": running both engines sequentially and comparing results.

## Phase 3: Simple Exporter Conversion
*Strategy: Duplicate folder -> Convert Templates -> Update Code -> Verify -> Leave "2" folder active.*

- [x] **Task: Grammar Dict**
  - [x] Copy `exporter/grammar_dict` -> `exporter/grammar_dict2`.
  - [x] Implement `GrammarData` ViewModel mirroring `exporter/webapp/data_classes.py`.
  - [x] Convert templates to `.jinja`. Update code to use Jinja2.
  - [x] Verify 100% match against baseline.
- [x] **Task: Deconstructor**
  - [x] Copy `exporter/deconstructor` -> `exporter/deconstructor2`.
  - [x] Implement `DeconstructorData` ViewModel mirroring `exporter/webapp/data_classes.py`.
  - [x] Convert templates to `.jinja`. Update code to use Jinja2.
  - [x] Verify 100% match against baseline.
- [x] **Task: Kindle**
  - [x] Copy `exporter/kindle` -> `exporter/kindle2`.
  - [x] Port Kindle formatting logic into ViewModels.
  - [x] Convert templates to `.jinja`. Update code. Verify 100% match.

## Phase 4: GoldenDict Re-Architecture (The Big One)
*Goal: Move to Master Templates and Unified Data Classes.*

- [x] **Task: Setup GoldenDict2**
  - [x] Copy `exporter/goldendict` -> `exporter/goldendict2`.
- [x] **Task: Headwords Export**
  - [x] Implement `HeadwordData` in `exporter/goldendict2/data_classes.py`.
  - [x] Create Master Template `exporter/goldendict2/templates/dpd_headword.jinja`.
  - [x] Refactor `export_dpd.py` to use Jinja2 and `HeadwordData`.
  - [x] Verify 100% match.
- [x] **Task: Roots Export**
  - [x] Implement `RootsData` in `exporter/goldendict2/data_classes.py`.
  - [x] Create Master Template `exporter/goldendict2/templates/root_definition.jinja` (consolidating root partials).
  - [x] Refactor `export_roots.py` to use Jinja2 and `RootsData`.
  - [x] Verify 100% match.
- [x] **Task: EPD Export**
  - [x] Implement `EpdData` ViewModel.
  - [x] Convert `epd.html` to `epd.jinja`.
  - [x] Refactor `export_epd.py`.
  - [x] Verify 100% match.
- [x] **Task: Variants & Spelling Export**
  - [x] Implement `VariantData` and `SpellingData` ViewModels.
  - [x] Convert templates to `.jinja`.
  - [x] Refactor `export_variant_spelling.py`.
  - [x] Verify 100% match.
- [x] **Task: Help & Abbreviations Export**
  - [x] Implement `HelpData` and `AbbreviationsData` ViewModels.
  - [x] Convert templates to `.jinja`.
  - [x] Refactor `export_help.py`.
  - [x] Verify 100% match.

## Phase 5: TPR Independence
- [x] **Task: Setup TPR2**
  - [x] Copy `exporter/tpr` -> `exporter/tpr2`.
- [x] **Task: Independent Template**
  - [x] Create `exporter/tpr2/templates/tpr_headword.jinja`.
  - [x] Hardcode the specific TPR HTML structure directly into the template (independent of GoldenDict).
- [x] **Task: Remove Regex**
  - [x] Update `tpr2/tpr_exporter.py` to render the template and *skip* the regex post-processing.
- [x] **Task: Verify**
  - [x] Confirm output matches the baseline exactly.

## Phase 6: Final Verification
- [x] **Task: Full Suite Run**
  - [x] Run all `*2` exporters.
  - [x] Compare against `baseline_outputs`.
  - [x] Ensure no regressions.

## Phase 7: Cleanup and Switchover (DANGER ZONE)
*Requirement: Explicit User Approval needed before starting this phase.*

- [ ] **Task: Archive Originals**
  - [ ] Move `goldendict`, `tpr`, etc. to `exporter/archive/`.
- [ ] **Task: Promote New Versions**
  - [ ] Rename `goldendict2` -> `goldendict`.
  - [ ] Rename `tpr2` -> `tpr`.
  - [ ] (Etc for all exporters).
- [ ] **Task: Remove Mako**
  - [ ] Remove `mako` from `pyproject.toml`.
  - [ ] Verify everything runs without Mako installed.
