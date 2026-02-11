# Plan: Extract Other Dictionaries into Standalone Repository

---

## Phase 0: Worktree Setup & Branch Isolation

- [x] Task: Create a dedicated Git worktree branch for the refactor
    - [x] Create branch `refactor/other-dictionaries` from `main`
    - [x] Set up Git worktree at `../dpd-db-other-dicts-worktree`
    - [x] Verify worktree is functional and isolated from main working directory

**Phase 0 Verification:**
```bash
# Must show the new worktree listed
git worktree list
# Must be on the correct branch
cd ../dpd-db-other-dicts-worktree && git branch --show-current
# Must show "refactor/other-dictionaries"
```

- [x] Task: Conductor - User Manual Verification 'Worktree Setup & Branch Isolation' (Protocol in workflow.md)

---

## Phase 1: New Repository Scaffolding

- [x] Task: Initialize the `other-dictionaries` repo structure
    - [x] Create `resources/other-dictionaries/` directory in the worktree
    - [x] Create `pyproject.toml` with project metadata and dependencies
    - [x] Create root `.gitignore`
    - [x] Create root `README.md`
- [x] Task: Create the directory scaffold
    - [x] Create directories for all 15 dictionaries
    - [x] Create `vendor/dpd_tools/` with `__init__.py`
    - [x] Create `scripts/` directory
    - [x] Create `tests/` directory
    - [x] Create `build/` directories (gitignored)
    - [x] Copy `bmp_files/` directory

**Phase 1 Verification:**
```bash
cd resources/other-dictionaries

# Verify all 15 dictionary dirs exist in dictionaries/
for d in abt bhs bold_def cone cpd dhammika dppn dpr mw peu simsapa sin_eng_sin vri whitney wordnet; do
  [ -d "dictionaries/$d" ] && echo "✓ dictionaries/$d" || echo "✗ MISSING: dictionaries/$d"
done

# Verify scaffold
[ -f pyproject.toml ] && echo "✓ pyproject.toml" || echo "✗ MISSING"
[ -f .gitignore ] && echo "✓ .gitignore" || echo "✗ MISSING"
[ -f README.md ] && echo "✓ README.md" || echo "✗ MISSING"
[ -d vendor/dpd_tools ] && echo "✓ vendor/dpd_tools/" || echo "✗ MISSING"
[ -d scripts ] && echo "✓ scripts/" || echo "✗ MISSING"
[ -d tests ] && echo "✓ tests/" || echo "✗ MISSING"
[ -d bmp_files ] && echo "✓ bmp_files/" || echo "✗ MISSING"
[ -d build ] && echo "✓ build/" || echo "✗ MISSING"

# Verify pyproject.toml is valid
python -c "import tomllib; tomllib.load(open('pyproject.toml','rb')); print('✓ pyproject.toml is valid')"
```

- [x] Task: Conductor - User Manual Verification 'New Repository Scaffolding' (Protocol in workflow.md)

---

## Phase 2: Vendor DPD Tools

- [x] Task: Write Tests — Verify vendored tools are importable and functional
    - [x] Write `tests/test_vendor_imports.py` that imports all required modules
    - [x] Run tests and confirm they fail (Red Phase)
- [x] Task: Implement — Copy and adapt DPD tools
    - [x] Identify all transitive dependencies of the required tool modules
    - [x] Copy required modules into `vendor/dpd_tools/`
    - [x] Create `vendor/dpd_tools/paths.py` — new path resolver for repo structure
    - [x] Fix internal imports within vendored tools
    - [x] Run tests and confirm they pass (Green Phase)
- [x] Task: Create `scripts/sync.py` — Vendor refresh script
    - [x] Implement function to copy tools from a DPD repo path into `vendor/dpd_tools/`
    - [x] Accept DPD repo path as CLI argument

**Phase 2 Verification:**
```bash
cd resources/other-dictionaries

# Run import tests
uv run pytest tests/test_vendor_imports.py -v

# Verify all key modules import correctly
uv run python -c "
from vendor.dpd_tools.goldendict_exporter import DictEntry, DictInfo, DictVariables, export_to_goldendict_with_pyglossary
from vendor.dpd_tools.mdict_exporter import export_to_mdict
from vendor.dpd_tools.niggahitas import add_niggahitas
from vendor.dpd_tools.printer import printer
from vendor.dpd_tools.pali_sort_key import pali_sort_key
from vendor.dpd_tools.sanskrit_translit import slp1_translit
print('✓ All vendor imports successful')
"

# Verify sync script runs without error
uv run python scripts/sync.py --dpd-path ../../ --dry-run
```

- [x] Task: Conductor - User Manual Verification 'Vendor DPD Tools' (Protocol in workflow.md)

---

## Phase 3: Source Data Independence

- [x] Task: Write Tests — Verify source data extraction produces valid TSV
    - [x] Write `tests/test_source_data.py` with schema validation for each extracted TSV
    - [x] Run tests and confirm they fail (Red Phase)
- [x] Task: Implement — Create source data extraction scripts
    - [x] Copy `bold_definitions.tsv` from `db/bold_definitions/` to `dictionaries/bold_def/source/`
    - [x] Download PEU dump from https://pm12e.pali.tools/dump to `dictionaries/peu/source/peu_dump.js`
    - [x] Simsapa & MW: marked as requiring external Simsapa DB (skipped tests)
    - [x] Run tests and confirm they pass (Green Phase)
- [ ] Task: Integrate extraction into `scripts/sync.py` (deferred to Phase 6)

**Phase 3 Verification:**
```bash
cd resources/other-dictionaries

# Run source data tests
uv run pytest tests/test_source_data.py -v

# Verify each source file exists
ls -la dictionaries/bold_def/source/bold_definitions.tsv
ls -la dictionaries/peu/source/peu_dump.js
```

- [x] Task: Conductor - User Manual Verification 'Source Data Independence' (Protocol in workflow.md)

---

## Phase 4: Migrate & Refactor Exporters (Batch 1 — Simple Exporters)

Migrate: bhs, cpd, dpr, whitney, abt, dppn, sin_eng_sin

- [x] Task: Write Tests — Verify batch 1 exporters produce valid DictEntry lists
    - [x] Write `tests/test_exporters_batch1.py`
    - [x] Run tests and confirm they fail (Red Phase)
- [x] Task: Implement — Migrate and refactor batch 1 exporters
    - [x] Copy source files, CSS, and Python scripts to `dictionaries/<name>/`
    - [x] Refactor imports: `from tools.xxx` → `from vendor.dpd_tools.xxx`
    - [x] Refactor all paths to be repo-relative using `RepoPaths`
    - [x] Update output paths to `build/`
    - [x] Run tests and confirm they pass (Green Phase)

**Phase 4 Verification:**
```bash
cd resources/other-dictionaries

# Run batch 1 tests
uv run pytest tests/test_exporters_batch1.py -v

# Verify each exporter can be imported
for mod in dictionaries.bhs.bhs dictionaries.cpd.cpd dictionaries.dpr.dpr dictionaries.whitney.whitney dictionaries.abt.abt_glossary dictionaries.dppn.dppn dictionaries.sin_eng_sin.sin_eng_sin; do
  uv run python -c "import importlib; m=importlib.import_module('$mod'); print(f'✓ $mod imported')" 2>&1
done
```

- [x] Task: Conductor - User Manual Verification 'Migrate & Refactor Exporters (Batch 1)' (Protocol in workflow.md)

---

## Phase 5: Migrate & Refactor Exporters (Batch 2 — Database-Dependent Exporters)

Migrate: bold_def, peu, simsapa, mw, cone

- [x] Task: Write Tests — Verify batch 2 exporters produce valid DictEntry lists
    - [x] Write `tests/test_exporters_batch2.py`
    - [x] Run tests and confirm they fail (Red Phase)
- [x] Task: Implement — Migrate and refactor batch 2 exporters
    - [x] Copy exporters to `dictionaries/<name>/`
    - [x] Refactor each to read from bundled TSV/JSON source files
    - [x] Refactor imports and paths
    - [x] Run tests and confirm they pass (Green Phase)
- [x] Task: Add database extraction scripts for simsapa and mw
    - [x] Create `dictionaries/simsapa/update_source.py` to copy JSON from DPD repo
    - [x] Create `dictionaries/mw/update_source.py` to copy JSON from DPD repo
    - [x] Update exporters to read from JSON instead of TSV
    - [ ] Integrate into `scripts/sync.py` (optional)

**Phase 5 Verification:**
```bash
cd resources/other-dictionaries

# Run batch 2 tests
uv run pytest tests/test_exporters_batch2.py -v

# Verify each exporter can be imported
for mod in dictionaries.bold_def.bold_definitions dictionaries.peu.peu dictionaries.simsapa.simsapa_combined dictionaries.mw.mw_from_simsapa dictionaries.cone.cone; do
  uv run python -c "import importlib; m=importlib.import_module('$mod'); print(f'✓ $mod imported')" 2>&1
done
```

- [x] Task: Conductor - User Manual Verification 'Migrate & Refactor Exporters (Batch 2)' (Protocol in workflow.md)

---

## Phase 6: Build Pipeline & Export All

- [x] Task: Write Tests — Verify export_all orchestrator
    - [x] Write `tests/test_export_all.py`
    - [x] Run tests and confirm they fail (Red Phase)
- [x] Task: Implement — Create unified build pipeline
    - [x] Create `scripts/export_all.py`
    - [x] Add per-dictionary `README.md` files
    - [x] Run tests and confirm they pass (Green Phase)
- [x] Task: End-to-end build verification

**Phase 6 Verification:**
```bash
cd resources/other-dictionaries

# Run export_all tests
uv run pytest tests/test_export_all.py -v

# Full build (this will take a while)
uv run python scripts/export_all.py

# Count output files and compare to expected
echo "GoldenDict outputs:"
ls -lh build/goldendict/*.zip 2>/dev/null | wc -l
echo "MDict outputs:"
ls -lh build/mdict/*.zip 2>/dev/null | wc -l

# Expected: ~12 zip files in each directory
# Compare file list against original
diff <(ls ../../exporter/other_dictionaries/goldendict/ | sort) <(ls build/goldendict/ | sort)
```

- [x] Task: Conductor - User Manual Verification 'Build Pipeline & Export All' (Protocol in workflow.md)

---

## Phase 7: DPD Submodule Integration

- [ ] Task: Implement — Integrate as submodule and clean up DPD (requires GitHub push)
    - [ ] Push `resources/other-dictionaries/` to `digitalpalidictionary/other-dictionaries`
    - [ ] Initialize submodule in `.gitmodules`
    - [ ] Update DPD `tools/paths.py`
    - [ ] Update DPD `.gitignore`
    - [ ] Remove `exporter/other_dictionaries/` from DPD

**Phase 7 Verification:**
```bash
# From worktree root (DPD)
cd ../dpd-db-other-dicts-worktree

# Verify submodule is registered
grep "other-dictionaries" .gitmodules && echo "✓ Submodule registered" || echo "✗ MISSING"

# Verify old directory is gone
[ ! -d exporter/other_dictionaries ] && echo "✓ Old directory removed" || echo "✗ Still exists"

# Verify paths.py references new location
grep "resources/other-dictionaries" tools/paths.py | head -3

# Verify no stale references remain
grep -r "exporter/other_dictionaries" tools/ exporter/ --include="*.py" -l 2>/dev/null
# Should return nothing
```

- [ ] Task: Conductor - User Manual Verification 'DPD Submodule Integration' (Protocol in workflow.md)

---

## Phase 8: CI/CD & Auto-Versioning

- [x] Task: Write Tests — Verify version calculation logic
    - [x] Write `tests/test_version.py`
    - [x] Run tests and confirm they fail (Red Phase)
- [x] Task: Implement — GitHub Actions workflow & version management
    - [x] Create `.github/workflows/build-and-release.yml`
    - [x] Create `scripts/version.py`
    - [x] Run tests and confirm they pass (Green Phase)

**Phase 8 Verification:**
```bash
cd resources/other-dictionaries

# Run version tests
uv run pytest tests/test_version.py -v

# Verify version script works
uv run python scripts/version.py
# Should output "v1.0.0" (no previous tags)

# Validate GitHub Actions workflow syntax
uv run python -c "
import yaml
with open('.github/workflows/build-and-release.yml') as f:
    wf = yaml.safe_load(f)
print(f'✓ Workflow is valid YAML')
print(f'  Jobs: {list(wf.get(\"jobs\", {}).keys())}')
print(f'  Trigger: {list(wf.get(\"on\", {}).keys())}')
"
```

- [x] Task: Conductor - User Manual Verification 'CI/CD & Auto-Versioning' (Protocol in workflow.md)

---

## Final: Documentation & Cleanup

- [x] Task: Update documentation
    - [x] Update DPD root README if it references `exporter/other_dictionaries/`
    - [x] Ensure `other-dictionaries` repo README is complete
    - [x] Update DPD `docs/` if relevant
- [x] Task: Lint and format all code
    - [x] `uv run ruff check --fix` on all new/modified Python files
    - [x] `uv run ruff format` on all new/modified Python files
- [x] Task: Final review and cleanup

**Final Verification:**
```bash
cd resources/other-dictionaries

# Run ALL tests
uv run pytest tests/ -v

# Lint check
uv run ruff check .
uv run ruff format --check .

# Verify no stale references in DPD
cd ../..  # back to DPD root
grep -rn "exporter/other_dictionaries" --include="*.py" --include="*.md" . 2>/dev/null | grep -v ".git/" | grep -v "__pycache__"
# Should return nothing (or only historical references in conductor/)
```
