# Track Specification: Flet 1.0 Migration (gui2 -> gui3)

## Overview
This track involves migrating the entire `gui2` Flet application to Flet 1.0 (Beta). The migration addresses a comprehensive list of breaking changes while refactoring the codebase toward Flet 1.0's modernized declarative patterns. A key architectural goal is to refactor "Page" and "View" classes from an inheritance-based model (`class MyView(ft.Column)`) to a composition-based model to isolate namespaces and improve maintainability. The work will be performed in a new branch and worktree named `gui3`.

## Breaking Changes Analysis (Exhaustive List)

### 1. Application Execution
- Replace all instances of `ft.app(target=main)` with `ft.run(main)`.
- **Affected Files:** `main.py`, `test_app.py`, and utility scripts.

### 2. Button Refactoring (High Impact)
- The `text` property on all buttons (`ElevatedButton`, `TextButton`, `OutlinedButton`, `IconButton`) is removed.
- **Fix:** Replace `text="Label"` with `content=ft.Text("Label")`.
- **Strategy:** Utilize or create reusable components (e.g., in `ui_utils.py`) to wrap this logic.

### 3. Alignment Enums
- Replace all lowercase alignment constants (e.g., `ft.alignment.center`) with uppercase enums (e.g., `ft.Alignment.CENTER`).

### 4. Icon Property Mapping
- Replace `Icon(name=...)` with `Icon(icon=...)`.
- Replace `IconButton(icon_name=...)` with `IconButton(icon=...)`.

### 5. Page & Services Lifecycle
- Rename `page.on_resized` to `page.on_resize`.
- Replace `page.client_storage` with `page.shared_preferences`.
- Move any non-UI services (`FilePicker`, `Audio`) to `page.services`.

### 6. Theme Engine Updates
- Remove legacy `Theme` properties: `primary_swatch`, `primary_color`, etc.
- Migrate to new Flet 1.0 Theme properties.

### 7. Method Suffix Removal
- Remove `_async` suffix from all Flet methods (e.g., `update_async` -> `update`).

## Functional Requirements
- **Branch/Worktree Isolation:** Create branch `gui3` and a git worktree at the project root.
- **Total Migration:** Every component in the app must be Flet 1.0 compatible.
- **Namespace Isolation (Architectural Refactor):** 
    - Refactor classes that currently extend `ft.Column` or other base controls to use **composition**.
    - These classes will now *contain* their layout controls rather than *being* them, isolating the page logic from the base control's namespace.
- **Reusable Components:** Leverage and expand reusable UI components to handle breaking changes centrally.
- **Functional Parity:** No features or lexicographer logic should be lost during migration.

## Non-Functional Requirements
- **Maintainability:** Cleaner code structure following "Composition over Inheritance".
- **Stability:** Zero regressions in logic or data handling.
- **Documentation:** Updated `README.md` in `gui3`.

## Acceptance Criteria
- [ ] Application successfully launches using Flet 1.0 in the `gui3` worktree.
- [ ] Page/View classes no longer extend `ft.Column` (namespace isolation verified).
- [ ] Every button label displays correctly (migrated to `content=ft.Text(...)`).
- [ ] Alignment and Iconography display correctly across all views.
- [ ] All page events and services are correctly mapped.
- [ ] Code passes `ruff check --fix` and `ruff format`.
- [ ] All underlying logic tests pass.
- [ ] Manual verification confirms no regressions in lexicographer workflows.

## Out of Scope
- Adding new functional features to the dictionary GUI.
- Database schema changes.
- Visual/UI layout testing (handled manually by the user).
