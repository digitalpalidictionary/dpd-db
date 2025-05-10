# Migration Plan: Tests Tab from PySimpleGUI to Flet

This document outlines the plan to migrate the "Tests" tab from the existing PySimpleGUI-based GUI to a new Flet-based GUI. The migration will be done incrementally, focusing on integrating into `gui2/test_app.py` first for isolated development and testing, and then into `gui2/main.py`.

## Phase 1: Initial Setup and Layout Migration

1.  **Prepare `gui2/test_app.py`:** ✔️
    *   Clear existing content in `gui2/test_app.py`. ✔️
    *   Set up a basic Flet application structure that can host the new "Tests" tab content. ✔️
    *   This will serve as a sandbox for developing and testing the new tab in isolation. ✔️

2.  **Analyze PySimpleGUI Layout (`gui/tab_db_tests.py`):** ✔️
    *   Identify all UI elements in the `tab_db_tests` layout. ✔️
    *   Map each PySimpleGUI element to its closest Flet equivalent. ✔️
        *   `sg.Text` -> `ft.Text`
        *   `sg.Button` -> `ft.ElevatedButton`, `ft.TextButton`, or `ft.IconButton`
        *   `sg.Input` -> `ft.TextField`
        *   `sg.Combo` -> `ft.Dropdown`
        *   `sg.Table` -> `ft.DataTable`
        *   Layout structures (lists of lists) -> `ft.Column`, `ft.Row`, `ft.Container`

3.  **Replicate Layout in Flet (`gui2/test_app.py` initially, then `gui2/tests_tab_view.py`):** ✔️
    *   **Row 1 (Buttons):**
        *   Run Tests, Stop Tests, Edit Tests, Run Ru Tests. ✔️
    *   **Row 2 (Test Info):**
        *   Test Number (Text), Test Name (TextField), Iterations (TextField). ✔️
    *   **Rows 3-8 (Test Criteria 1-6):**
        *   Label (Text), Search Column (TextField), Search Sign (Dropdown), Search String (TextField). ✔️
    *   **Row 9 (Display Fields):**
        *   Label (Text), Display 1 (TextField), Display 2 (TextField), Display 3 (TextField). ✔️
    *   **Row 10 (Error Info):**
        *   Label (Text), Error Column (TextField), Exceptions (Dropdown - initially empty). ✔️
    *   **Row 11 (Action Buttons):**
        *   Update Tests, Add New Test, Delete Test. ✔️
    *   **Row 12 (Results Summary):**
        *   Labels (Text) for "displaying X of Y results". ✔️
    *   **Row 13 (Results Table):**
        *   Label (Text), DataTable (initially empty with placeholder headings). ✔️
    *   **Row 14 (Add Exception):**
        *   Label (Text), Add Exception (Dropdown - initially empty), Add Button, DB Query (TextField), DB Query Copy Button. ✔️
    *   **Row 15 (Next Button):**
        *   Next Button (full width). ✔️
    *   Focus on visual structure first. Functionality will be added later. ✔️
    *   Use `ft.Row`, `ft.Column`, and `ft.Container` to arrange elements. ✔️
    *   (Note: `ref` attributes were initially considered, then instance attributes were used directly). ✔️

4.  **Refactor to Class-based Component (`gui2/tests_tab_view.py`):** ✔️
    *   Convert the layout code into a reusable Flet component class (`TestsTabView(ft.Column)`). ✔️
    *   This class encapsulates all UI elements as instance attributes. ✔️
    *   Update `gui2/test_app.py` to instantiate and display this `TestsTabView` component. ✔️
    *   Update `TestsTabView` to accept `page` and `toolkit` in its constructor for consistency and future use. ✔️

5.  **Layout Review and Adjustments:** ✔️
    *   Thoroughly review the Flet layout against the original PySimpleGUI layout. ✔️
    *   Make necessary adjustments to sizing, spacing, alignment, and styling (e.g., label colors, text field label styles, field widths). ✔️
    *   Ensure all static elements are correctly displayed. ✔️

## Phase 2: Functionality Migration (High-Level)

*(This phase will be detailed further as Phase 1 progresses)*

1.  **Event Handling:**
    *   Connect button clicks (`on_click`) to placeholder functions within the `TestsTabView` class.
    *   Implement placeholder `on_change` and other relevant event handlers (e.g., `on_submit`) for TextFields and Dropdowns where necessary.
2.  **Data Binding/State Management:**
    *   Determine how data from TextFields and Dropdowns will be read.
    *   Plan how to update elements (e.g., Text, DataTable) based on application logic.
3.  **Porting Logic from `gui/functions_tests.py`:**
    *   Start with simpler functions and gradually move to more complex ones.
    *   Adapt PySimpleGUI-specific window update logic to Flet's way of updating UI elements.
    *   Initial focus will be on the `db_internal_tests` related functionality as it's the primary part of the tab.

## Phase 3: Integration into `gui2/main.py`

1.  **Import `TestsTabView` in `gui2/main.py`:** ✔️
    *   Add `from gui2.tests_tab_view import TestsTabView`. ✔️
2.  **Instantiate `TestsTabView` in `App.__init__`:** ✔️
    *   Create an instance: `self.tests_tab_view: TestsTabView = TestsTabView(self.page, self.toolkit)`. ✔️
3.  **Add `ft.Tab` to `ft.Tabs` control:** ✔️
    *   Include a new `ft.Tab(text="Tests", content=self.tests_tab_view)` in the `tabs` list. ✔️

---

Next step: Start Phase 2: Functionality Migration, beginning with Event Handling (Phase 2, Step 1).
