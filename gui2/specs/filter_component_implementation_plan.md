# Filter Component Implementation Plan

## Overview
This document provides a detailed implementation plan for the FilterComponent, including code snippets and architectural decisions.

## 1. FilterComponent Class Structure

### Basic Class Definition
```python
import flet as ft
import re
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from db.models import DpdHeadword
from gui2.toolkit import ToolKit


class FilterComponent(ft.Column):
    """A modular filter component for DPD database filtering."""
    
    def __init__(self, page: ft.Page, toolkit: ToolKit) -> None:
        super().__init__(expand=True, spacing=5, controls=[])
        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit
        
        # State management
        self.active_filters: List[Dict[str, str]] = []
        self.display_columns: List[str] = []
        self.result_limit: int = 0
        self.filtered_results: List[DpdHeadword] = []
        
        # UI Controls
        self.filter_rows: List[ft.Row] = []
        self.column_dropdowns: List[ft.Dropdown] = []
        self.regex_inputs: List[ft.TextField] = []
        self.display_column_selector: ft.Dropdown = None
        self.limit_input: ft.TextField = None
        self.results_table: ft.DataTable = None
        
        self._build_ui()
```

## 2. UI Building

### Main UI Structure
```python
def _build_ui(self) -> None:
    """Build the main UI structure for the filter component."""
    
    # Data Filters Section
    data_filters_section = self._create_data_filters_section()
    
    # Display Filters Section
    display_filters_section = self._create_display_filters_section()
    
    # Results Limit Section
    limit_section = self._create_limit_section()
    
    # Action Buttons
    buttons_section = self._create_buttons_section()
    
    # Results Table
    results_section = self._create_results_section()
    
    # Assemble all sections
    self.controls.extend([
        data_filters_section,
        display_filters_section,
        limit_section,
        buttons_section,
        results_section
    ])
```

### Data Filters Section
```python
def _create_data_filters_section(self) -> ft.Column:
    """Create the data filters section with add/remove functionality."""
    
    # Initial filter row
    initial_filter_row = self._create_filter_row()
    self.filter_rows.append(initial_filter_row)
    
    return ft.Column([
        ft.Text("Data Filters", size=20, weight=ft.FontWeight.BOLD),
        initial_filter_row,
        ft.Row([
            ft.ElevatedButton("Add Filter", on_click=self._add_filter_row),
            ft.ElevatedButton("Remove Filter", on_click=self._remove_filter_row)
        ])
    ])
```

### Filter Row Creation
```python
def _create_filter_row(self) -> ft.Row:
    """Create a single filter row with column selector and regex input."""
    
    # Get all DpdHeadword column names
    column_names = [column.name for column in DpdHeadword.__table__.columns]
    
    # Create column dropdown
    column_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(col) for col in column_names],
        width=200,
        hint_text="Select Column"
    )
    
    # Create regex input
    regex_input = ft.TextField(
        width=300,
        hint_text="Enter regex pattern"
    )
    
    # Store references
    self.column_dropdowns.append(column_dropdown)
    self.regex_inputs.append(regex_input)
    
    return ft.Row([
        column_dropdown,
        regex_input
    ])
```

## 3. Filtering Logic

### Apply Filters Method
```python
def _apply_filters(self, e: ft.ControlEvent) -> None:
    """Apply all active filters and display results."""
    
    try:
        # Build SQLAlchemy query based on filters
        query = self.toolkit.db_manager.db_session.query(DpdHeadword)
        
        # Apply data filters
        filter_conditions = []
        for i, (column_dropdown, regex_input) in enumerate(zip(self.column_dropdowns, self.regex_inputs)):
            if column_dropdown.value and regex_input.value:
                # Get the column attribute
                column_attr = getattr(DpdHeadword, column_dropdown.value)
                # Create regex condition
                try:
                    pattern = re.compile(regex_input.value)
                    filter_conditions.append(column_attr.regexp_match(regex_input.value))
                except re.error as ex:
                    self._show_error(f"Invalid regex in filter {i+1}: {ex}")
                    return
        
        # Apply all conditions with AND
        if filter_conditions:
            query = query.filter(and_(*filter_conditions))
        
        # Apply limit if set
        if self.result_limit > 0:
            query = query.limit(self.result_limit)
        
        # Execute query
        self.filtered_results = query.all()
        
        # Update results display
        self._update_results_table()
        
        # Show success message
        self._show_message(f"Found {len(self.filtered_results)} results")
        
    except Exception as ex:
        self._show_error(f"Error applying filters: {ex}")
```

## 4. Display Filtering

### Display Column Selection
```python
def _create_display_filters_section(self) -> ft.Column:
    """Create the display filters section."""
    
    # Get all column names for display selection
    column_names = [column.name for column in DpdHeadword.__table__.columns]
    
    # Create multi-select dropdown
    self.display_column_selector = ft.Dropdown(
        options=[ft.dropdown.Option(col) for col in column_names],
        width=400,
        hint_text="Select columns to display (leave empty for all)",
        multiselect=True
    )
    
    return ft.Column([
        ft.Text("Display Filters", size=20, weight=ft.FontWeight.BOLD),
        ft.Row([self.display_column_selector])
    ])
```

## 5. Result Limiting

### Limit Input Section
```python
def _create_limit_section(self) -> ft.Column:
    """Create the result limit section."""
    
    self.limit_input = ft.TextField(
        label="Result Limit",
        hint_text="0 for all results",
        width=200,
        keyboard_type=ft.KeyboardType.NUMBER,
        value="0"
    )
    
    return ft.Column([
        ft.Text("Results Limit", size=20, weight=ft.FontWeight.BOLD),
        ft.Row([self.limit_input])
    ])
```

## 6. Results Display

### Results Table Creation
```python
def _create_results_section(self) -> ft.Column:
    """Create the results display section."""
    
    self.results_table = ft.DataTable(
        columns=[],
        rows=[],
        border=ft.border.all(2, ft.Colors.BLACK),
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
        vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
        heading_row_color=ft.Colors.GREY_200
    )
    
    return ft.Column([
        ft.Text("Results", size=20, weight=ft.FontWeight.BOLD),
        ft.Row([self.results_table], scroll=ft.ScrollMode.AUTO)
    ])
```

### Results Table Update
```python
def _update_results_table(self) -> None:
    """Update the results table with filtered data."""
    
    # Determine which columns to display
    selected_columns = self.display_column_selector.value or []
    if not selected_columns:
        # If no columns selected, show all
        selected_columns = [column.name for column in DpdHeadword.__table__.columns]
    
    # Create table columns
    table_columns = [
        ft.DataColumn(ft.Text(col.replace("_", ").title())) 
        for col in selected_columns
    ]
    
    # Create table rows
    table_rows = []
    for record in self.filtered_results:
        cells = []
        for col in selected_columns:
            value = getattr(record, col, "")
            cells.append(ft.DataCell(ft.Text(str(value)[:50])))  # Truncate long values
        table_rows.append(ft.DataRow(cells=cells))
    
    # Update table
    self.results_table.columns = table_columns
    self.results_table.rows = table_rows
    
    # Refresh UI
    self.page.update()
```

## 7. Data Editing

### Editable Results Table
```python
def _create_editable_results_section(self) -> ft.Column:
    """Create an editable results display section."""
    
    # This would be a more complex implementation with editable cells
    # For now, we'll focus on the basic display and add editing later
    
    return self._create_results_section()
```

## 8. Save Functionality

### Save Method
```python
def _save_changes(self, e: ft.ControlEvent) -> None:
    """Save any changes back to the database."""
    
    try:
        # In a more complex implementation, we would track changes
        # For now, we'll just show a message
        self._show_message("Save functionality would be implemented here")
        
        # Example of how to use DatabaseManager to save:
        # success, error = self.toolkit.db_manager.update_word_in_db(edited_word)
        # if success:
        #     self._show_message("Changes saved successfully")
        # else:
        #     self._show_error(f"Failed to save changes: {error}")
        
    except Exception as ex:
        self._show_error(f"Error saving changes: {ex}")
```

## 9. Helper Methods

### UI Helpers
```python
def _add_filter_row(self, e: ft.ControlEvent) -> None:
    """Add a new filter row."""
    new_row = self._create_filter_row()
    self.filter_rows.append(new_row)
    
    # Insert before the buttons row
    self.controls[0].controls.insert(-1, new_row)
    self.page.update()

def _remove_filter_row(self, e: ft.ControlEvent) -> None:
    """Remove the last filter row."""
    if len(self.filter_rows) > 1:
        removed_row = self.filter_rows.pop()
        self.column_dropdowns.pop()
        self.regex_inputs.pop()
        
        self.controls[0].controls.remove(removed_row)
        self.page.update()

def _show_message(self, message: str) -> None:
    """Show a message to the user."""
    # This would typically update a status bar or show a snackbar
    print(f"Message: {message}")

def _show_error(self, error: str) -> None:
    """Show an error message to the user."""
    # This would typically show an error dialog or update in red
    print(f"Error: {error}")
```

## 10. Integration with FilterTabView

### Updated FilterTabView
```python
# In filter_tab_view.py
import flet as ft
from gui2.toolkit import ToolKit
from gui2.components.filter_component import FilterComponent  # New import


class FilterTabView(ft.Column):
    """Filter tab for database filtering functionality."""

    def __init__(self, page: ft.Page, toolkit: ToolKit) -> None:
        super().__init__(expand=True, spacing=5, controls=[])
        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit

        # Create and add the filter component
        self.filter_component = FilterComponent(self.page, self.toolkit)
        
        # Build UI structure
        self.controls.extend([
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    "Database Filter", size=20, weight=ft.FontWeight.BOLD
                                ),
                            ]
                        ),
                        self.filter_component,
                    ]
                ),
                padding=10,
            )
        ])
```

## Implementation Sequence

1. Create the basic FilterComponent class structure
2. Implement UI building methods
3. Add data filtering logic with SQLAlchemy
4. Implement display filtering
5. Add result limiting functionality
6. Create results display
7. Add data editing capabilities
8. Implement save functionality
9. Integrate with FilterTabView
10. Test and refine

## Dependencies to Consider

- Flet for UI components
- SQLAlchemy for database operations
- Existing DatabaseManager for session handling
- DpdHeadword model for column definitions

## Error Handling Considerations

- Invalid regex patterns
- Database connection issues
- Validation errors on save
- Empty or invalid filter conditions
- Large result sets that might impact performance

## Performance Considerations

- Efficient querying with selected columns only
- Pagination for large result sets
- Caching of frequently used queries
- Asynchronous operations for better UI responsiveness