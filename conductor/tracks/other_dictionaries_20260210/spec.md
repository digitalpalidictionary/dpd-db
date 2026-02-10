# Spec: Extract Other Dictionaries into Standalone Repository

## Overview

Refactor `exporter/other_dictionaries/` from the DPD monorepo into its own standalone GitHub repository (`digitalpalidictionary/other-dictionaries`), consumed as a Git submodule at `resources/other-dictionaries` within DPD. The new repo will be fully self-contained, independently buildable, and publish dictionary releases via GitHub Actions with automatic incremental versioning.

## Background

Currently, `exporter/other_dictionaries/` is a 2.3GB directory embedded in the DPD monorepo containing 16 auxiliary dictionary exporters. These exporters produce GoldenDict and MDict format dictionaries from various Pāḷi, Sanskrit, and Sinhala source data. They depend on DPD's `tools/` modules for export functionality and some query external databases (TPR, Simsapa, DPD DB) at build time. This tight coupling prevents independent development, testing, and automated releases.

## Functional Requirements

### FR-1: Repository Structure

The new `other-dictionaries` repo must restructure the current layout so that what is currently inside `code/` becomes the root:

```
other-dictionaries/
├── abt/                    # Ancient Buddhist Texts Glossary
├── bhs/                    # Buddhist Hybrid Sanskrit
├── bold_def/               # CST Bold Definitions
├── cone/                   # Margaret Cone Dictionary of Pāḷi
├── cpd/                    # Critical Pāḷi Dictionary
├── dhammika/               # Dhammika (data only, no exporter yet)
├── dppn/                   # Dict. of Pāḷi Proper Names
├── dpr/                    # DPR Analysis
├── mw/                     # Monier-Williams Sanskrit-English
├── peu/                    # Pali English Ultimate
├── simsapa/                # Simsapa Combined
├── sin_eng_sin/            # Sinhala-English-Sinhala
├── vri/                    # VRI (data only, no exporter yet)
├── whitney/                # Whitney Sanskrit Roots
├── wordnet/                # WordNet (data only, incomplete)
├── vendor/dpd_tools/       # Vendored DPD tool modules
├── scripts/
│   ├── sync.py             # Refreshes vendor/ and source data
│   └── export_all.py       # Orchestrator (moved from code/)
├── tests/                  # All unit and integration tests
├── build/                  # All build output (goldendict, mdict)
├── bmp_files/              # Dictionary icons
├── .github/workflows/      # CI/CD
├── .gitignore
├── pyproject.toml
└── README.md
```

### FR-2: Dependency Vendoring

- DPD tool modules required by exporters must be copied into `vendor/dpd_tools/`.
- Required modules (identified from all exporters):
  - `tools.goldendict_exporter` → `vendor/dpd_tools/goldendict_exporter.py`
  - `tools.mdict_exporter` → `vendor/dpd_tools/mdict_exporter.py`
  - `tools.niggahitas` → `vendor/dpd_tools/niggahitas.py`
  - `tools.printer` → `vendor/dpd_tools/printer.py`
  - `tools.paths` → replaced with a local `paths.py` tailored to the new repo structure
  - `tools.configger` → `vendor/dpd_tools/configger.py`
  - `tools.pali_sort_key` → `vendor/dpd_tools/pali_sort_key.py`
  - `tools.sanskrit_translit` → `vendor/dpd_tools/sanskrit_translit.py`
- Any transitive dependencies of these tools must also be vendored.
- `vendor/dpd_tools/paths.py` must be rewritten to reflect the new repo's directory structure (e.g., output to `build/goldendict/`, `build/mdict/`).

### FR-3: Source Data Independence

Exporters that currently query live external databases must be refactored to read from standalone bundled source files:

| Exporter | Current Source | New Source |
|----------|---------------|------------|
| `bold_def` | Live DPD SQLite DB (`db.models.BoldDefinition`) | Pre-exported JSON in `bold_def/source/` |
| `peu` | Live TPR SQLite DB | Pre-exported JSON in `peu/source/` |
| `simsapa` | Live Simsapa SQLite DB | Pre-exported JSON in `simsapa/source/` |
| `mw` | Live Simsapa SQLite DB | Pre-exported JSON in `mw/source/` |

- Each exporter must have an `update_source.py` (or equivalent mechanism via `scripts/sync.py`) that can re-extract data from the upstream source when needed.
- `scripts/sync.py` must handle both vendor tools sync AND source data sync in a single command.

### FR-4: Import Refactoring

- All Python exporters must update their imports from `from tools.xxx import ...` to `from vendor.dpd_tools.xxx import ...` (or equivalent).
- All hardcoded paths (e.g., `"exporter/other_dictionaries/code/abt/CPED.csv"`) must be updated to use the new repo-relative paths.
- All `ProjectPaths()` references must be replaced with the new local paths module.

### FR-5: Build Output

- All exporters must output to a unified `build/` directory:
  - `build/goldendict/` — GoldenDict .zip files
  - `build/mdict/` — MDict .zip files
- The `build/` directory must be gitignored.

### FR-6: Git Submodule Integration

- The new repo must be registered as a Git submodule in DPD at `resources/other-dictionaries`.
- The old `exporter/other_dictionaries/` directory must be removed from DPD.
- DPD's `.gitignore` entries for `exporter/other_dictionaries/` must be cleaned up.
- DPD's `tools/paths.py` path definitions for other_dictionaries must be updated to point to `resources/other-dictionaries/`.

### FR-7: GitHub Actions CI/CD

- A GitHub Action workflow that:
  1. Checks out the `other-dictionaries` repo
  2. Runs `scripts/sync.py` (or uses pre-vendored/pre-bundled data)
  3. Builds all dictionaries via `scripts/export_all.py`
  4. Publishes build artifacts as a GitHub Release

### FR-8: Automatic Incremental Versioning

- Every new release must automatically increment the patch version (e.g., `v1.0.0` → `v1.0.1` → `v1.0.2`).
- The version must be derived from the latest existing release tag (not from a file).
- If no previous release exists, start at `v1.0.0`.

### FR-9: Work Tree Isolation

- All work must be performed in a Git worktree so the current state of the DPD repo is not disturbed.
- The worktree branch should be dedicated to this refactor.

## Non-Functional Requirements

- **NFR-1**: All Python files must pass `ruff check` and `ruff format`.
- **NFR-2**: The new repo must have its own `pyproject.toml` with required dependencies.
- **NFR-3**: Large source files (all under 100MB) are committed as-is — no Git LFS.
- **NFR-4**: Generated/build files (`build/`, `bulk_dump_html.html`, large JSON outputs) must be gitignored.
- **NFR-5**: Each dictionary directory should contain a brief `README.md` documenting its source, format, and how to run its exporter.

## Acceptance Criteria

1. **Independence**: `git clone other-dictionaries && python scripts/sync.py && python scripts/export_all.py` produces all dictionary files without requiring the DPD repo to be present (sync.py is pointed at a DPD path or downloads needed files).
2. **Submodule**: DPD can `git submodule update --init resources/other-dictionaries` and the exporters work from within DPD.
3. **CI/CD** Pushing to `main` (or manually triggering) the GitHub Action successfully builds all dictionaries and creates a versioned release.
4. **Versioning**: Each release automatically increments the patch number from the previous release.
5. **No Regression**: The output dictionaries (GoldenDict, MDict) are functionally identical to the current output.
6. **Clean DPD**: The old `exporter/other_dictionaries/` directory is fully removed from DPD, and all path references updated.

## Out of Scope

- Creating new dictionary exporters (e.g., finishing `wordnet`, `vri`, `dhammika`).
- Changing the export format or content of any existing dictionary.
- Modifying the DPD `tools/` modules themselves.
- Publishing the DPD tools as a standalone pip package.
- Migrating dictionaries to a different build system.
