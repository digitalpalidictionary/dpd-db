# Track Specification: Mac Dictionary Build Integration

## Overview
Integrate automated Mac native `.dictionary` file generation into the existing release workflow. The solution will generate dictionary source files (XML, CSS, plist) using Python on Linux, then compile the final `.dictionary` bundle using Apple's Dictionary Development Kit on macOS.

## Goals
- Automate Mac dictionary builds for every release without manual intervention
- Leverage existing release workflow infrastructure
- Provide native Dictionary.app integration for Mac users
- Maintain zero cost by using GitHub's free macOS runners for public repos

## Functional Requirements

### 1. Python Export Module (`exporter/apple_dictionary/`)
- **Purpose**: Generate Apple Dictionary Development Kit compatible source files
- **Input**: DPD SQLite database
- **Output Files**:
  - `Dictionary.xml` - Dictionary entries in Apple's XML format with proper `d:entry`, `d:index` tags
  - `Dictionary.css` - Minimal stylesheet for entry styling
  - `Info.plist` - Dictionary metadata (name, version, copyright, identifier)
- **Features**:
  - Map DPD headwords to `d:index` elements for lookup
  - Include Pāḷi word, meaning, grammar info, and examples
  - Support for proper CSS styling using DPD branding colors and identity (similar to exporter/kobo/ approach)
  - Generate unique bundle identifier: `org.digitalpalidictionary.dpd`

### 2. GitHub Actions Workflow Integration
- **Integration**: Modify existing `.github/workflows/draft_release.yml`
- **Job Structure**:
  - **Job 1 - `build-linux`**: Existing build job + Apple Dictionary export
    - Export Apple Dictionary source files (XML, CSS, plist) to `exporter/share/apple_dictionary/`
    - Upload source files as artifacts for macOS job
    - Continue with existing exports (GoldenDict, MDict, Kindle, etc.)
  - **Job 2 - `build-macos`**: New job (depends on `build-linux`)
    - Download Apple Dictionary source artifacts
    - Clone Apple's Dictionary Development Kit
    - Run `make` to compile `.dictionary` bundle
    - Upload `.dictionary` as artifact
  - **Job 3 - `create-release`**: Final job (depends on both build jobs)
    - Download all artifacts from both jobs
    - Create draft release with all assets including `.dictionary`

### 3. Integration Points
- Workflow triggered by `workflow_dispatch` (same as existing draft release)
- Reuses existing database built in the Linux job
- All assets (including .dictionary) ready before release creation
- Atomic release - all formats available simultaneously

## Non-Functional Requirements
- **Cost**: Must use free GitHub Actions minutes (public repo = free macOS runners)
- **Performance**: Total workflow time under 15 minutes
- **Reliability**: Workflow must fail gracefully if dictionary compilation fails
- **Maintainability**: Clear separation between data generation (Python) and compilation (macOS)

## Acceptance Criteria
- [ ] Python script successfully generates valid Apple Dictionary XML format
- [ ] GitHub Actions workflow triggers automatically on release
- [ ] Linux job generates and uploads dictionary source artifacts
- [ ] macOS job downloads artifacts and compiles `.dictionary` bundle
- [ ] Compiled `.dictionary` file is attached to the GitHub release
- [ ] Generated dictionary works in Mac Dictionary.app
- [ ] Workflow completes within 15 minutes
- [ ] Zero cost (uses free GitHub Actions tier)

## Out of Scope
- Manual dictionary builds (fully automated only)
- Support for older macOS versions (target latest stable)
- Dictionary preferences/settings UI
- Auto-update mechanism for installed dictionaries
- Windows/Linux dictionary formats (separate track)
