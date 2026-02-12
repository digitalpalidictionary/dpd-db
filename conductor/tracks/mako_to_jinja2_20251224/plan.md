# Plan: Mako to Jinja2 Template Refactoring

## CRITICAL REQUIREMENTS

⚠️ **NEVER overwrite or edit existing folders/files directly.**  
✅ **ALWAYS work in duplicated folders (e.g., `exporter/goldendict2/`).**  
✅ **OUTPUT MATCHING IS MANDATORY (Binary/Hex Check).**  
✅ **WEBAPP ALIGNMENT:** GoldenDict must use `HeadwordData` (ViewModel) and a Master Template.

## Phase 1: Discovery and Baseline Capture ("Golden Masters")
- [ ] **Task: Baseline Capture**
  - [ ] Create `capture_baselines.py`.
  - [ ] Generate HTML samples for ALL exporters (GoldenDict, TPR, Kindle, etc.) using the *current* Mako code.
  - [ ] Store in `baseline_outputs/` (treat these as immutable Golden Masters).

## Phase 2: Setup
- [ ] **Task: Jinja2 Environment**
  - [ ] Create `exporter/jinja2_env.py` with `trim_blocks=True`, `lstrip_blocks=True`.
- [ ] **Task: Naming Convention**
  - [ ] Use `.jinja` extension for all new templates to enable VS Code syntax highlighting (via "Better Jinja" extension) and distinguish from Mako `.html` templates.
- [ ] **Task: Advanced Comparison Tools**
  - [ ] Create `verify_output.py`.
  - [ ] **Requirement:** Implement binary diffing (check for BOM, CRLF) to ensure byte-perfect matching.
  - [ ] Support "Shadow Testing": running both engines sequentially and comparing results.

## Phase 3: Simple Exporter Conversion
*Strategy: Duplicate folder -> Convert Templates -> Update Code -> Verify -> Leave "2" folder active.*

- [ ] **Task: Grammar Dict**
  - [ ] Copy `exporter/grammar_dict` -> `exporter/grammar_dict2`.
  - [ ] Implement `GrammarData` ViewModel mirroring `exporter/webapp/data_classes.py`.
  - [ ] Convert templates to `.jinja`. Update code to use Jinja2.
  - [ ] Verify 100% match against baseline.
- [ ] **Task: Deconstructor**
  - [ ] Copy `exporter/deconstructor` -> `exporter/deconstructor2`.
  - [ ] Implement `DeconstructorData` ViewModel mirroring `exporter/webapp/data_classes.py`.
  - [ ] Convert templates to `.jinja`. Update code to use Jinja2.
  - [ ] Verify 100% match against baseline.
- [ ] **Task: Kindle**
  - [ ] Copy `exporter/kindle` -> `exporter/kindle2`.
  - [ ] Port Kindle formatting logic into ViewModels.
  - [ ] Convert templates to `.jinja`. Update code. Verify 100% match.

## Phase 4: GoldenDict Re-Architecture (The Big One)
*Goal: Move to Master Templates and Unified Data Classes.*

- [ ] **Task: Setup GoldenDict2**
  - [ ] Copy `exporter/goldendict` -> `exporter/goldendict2`.
- [ ] **Task: Headwords Export**
  - [ ] Implement `HeadwordData` in `exporter/goldendict2/data_classes.py`.
  - [ ] Create Master Template `exporter/goldendict2/templates/dpd_headword.jinja`.
  - [ ] Refactor `export_dpd.py` to use Jinja2 and `HeadwordData`.
  - [ ] Verify 100% match.
- [ ] **Task: Roots Export**
  - [ ] Implement `RootsData` in `exporter/goldendict2/data_classes.py`.
  - [ ] Create Master Template `exporter/goldendict2/templates/root_definition.jinja` (consolidating root partials).
  - [ ] Refactor `export_roots.py` to use Jinja2 and `RootsData`.
  - [ ] Verify 100% match.
- [ ] **Task: EPD Export**
  - [ ] Implement `EpdData` ViewModel.
  - [ ] Convert `epd.html` to `epd.jinja`.
  - [ ] Refactor `export_epd.py`.
  - [ ] Verify 100% match.
- [ ] **Task: Variants & Spelling Export**
  - [ ] Implement `VariantData` and `SpellingData` ViewModels.
  - [ ] Convert templates to `.jinja`.
  - [ ] Refactor `export_variant_spelling.py`.
  - [ ] Verify 100% match.
- [ ] **Task: Help & Abbreviations Export**
  - [ ] Implement `HelpData` and `AbbreviationsData` ViewModels.
  - [ ] Convert templates to `.jinja`.
  - [ ] Refactor `export_help.py`.
  - [ ] Verify 100% match.

## Phase 5: TPR Independence
- [ ] **Task: Setup TPR2**
  - [ ] Copy `exporter/tpr` -> `exporter/tpr2`.
- [ ] **Task: Independent Template**
  - [ ] Create `exporter/tpr2/templates/tpr_headword.jinja`.
  - [ ] Hardcode the specific TPR HTML structure directly into the template (independent of GoldenDict).
- [ ] **Task: Remove Regex**
  - [ ] Update `tpr2/tpr_exporter.py` to render the template and *skip* the regex post-processing.
- [ ] **Task: Verify**
  - [ ] Confirm output matches the baseline exactly.

## Phase 6: Final Verification
- [ ] **Task: Full Suite Run**
  - [ ] Run all `*2` exporters.
  - [ ] Compare against `baseline_outputs`.
  - [ ] Ensure no regressions.

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
