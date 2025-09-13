# Filter Component Specification

## Overview
This document specifies the design and implementation of a modular filter component for the DPD database application. The component will allow users to filter database records based on various criteria, display selected columns, limit results, edit data, and save changes back to the database.

## Component Architecture

### FilterComponent Class
A reusable Flet component that can be integrated into different parts of the application.

```python
class FilterComponent(ft.Column):
    def __init__(self, page: ft.Page, toolkit: ToolKit) -> None:
        super().__init__(expand=True, spacing=5, controls=[])
        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit
        # Implementation details...
```

## Features

### 1. Data Filter
- Column picker listing all DpdHeadword model columns
- Regex input field for pattern matching
- Ability to add multiple filter conditions
- Support for AND/OR combinations (optional enhancement)

### 2. Display Filter
- Multi-select dropdown for choosing which columns to display
- Affects both UI display and database query optimization

### 3. Result Limiting
- Numeric input for limiting results (0 for all)
- Applied after other filters

### 4. Data Editing
- Editable table/grid view of filtered results
- Inline editing of cell values
- Validation before saving

### 5. Save Functionality
- Save button to persist changes to database
- Uses SQLAlchemy for database operations
- Follows patterns from DatabaseManager

## Implementation Plan

### Phase 1: Core Component Structure
1. Create FilterComponent class with basic UI structure
2. Implement column picker with all DpdHeadword attributes
3. Add regex input fields for filtering

### Phase 2: Filtering Logic
1. Implement SQLAlchemy query building based on filters
2. Add display column selection
3. Add result limiting functionality

### Phase 3: Data Editing and Saving
1. Create editable table view for results
2. Implement save functionality using DatabaseManager patterns
3. Add validation and error handling

### Phase 4: Integration and Testing
1. Integrate into filter_tab_view.py
2. Test with various filter combinations
3. Document usage and API

## UI Design

### Layout
```
+-------------------------------------------------------------+
| Data Filters                                                |
| [Column Selector] [Regex Input] [+] [Remove]                |
| [Column Selector] [Regex Input] [+] [Remove]                |
| ...                                                         |
+-------------------------------------------------------------+
| Display Filters                                             |
| [Multi-select Columns]                                      |
+-------------------------------------------------------------+
| Results Limit                                               |
| [Number Input] (0 for all)                                  |
+-------------------------------------------------------------+
| [Apply Filters] [Save Changes]                              |
+-------------------------------------------------------------+
| Results Table (Editable)                                    |
| +----+----+----+----+----+----+    |
| | ID | Col1 | Col2 | ... | Edit |                            |
| +----+----+----+----+----+----+----+    |
| | 1  | Val1 | Val2 | ... | [Edit] |                          |
| +----+----+----+----+----+    |
+-------------------------------------------------------------+
```

### Description of gui2/specs/filter_component_layout.png
The image `gui2/specs/filter_component_layout.png` depicts a user interface layout for a filter component. The layout is organized vertically into several distinct sections.

1.  **Data Filters**: This section is at the top and contains multiple rows, each with a "Column Selector" (likely a dropdown), a "Regex Input" field, an "Add" button (`[+]`), and a "Remove" button. This suggests the ability to add and remove multiple filtering conditions based on different columns and regular expressions.

2.  **Display Filters**: Below the Data Filters, this section features a "Multi-select Columns" control, indicating that users can choose which columns from the dataset to display in the results.

3.  **Results Limit**: This section contains a "Number Input" field, allowing users to specify the maximum number of results to be returned. A note "0 for all" clarifies its functionality.

4.  **Action Buttons**: A row with two buttons, "[Apply Filters]" and "[Save Changes]", is present. "Apply Filters" would trigger the filtering process, while "Save Changes" would persist any edits made to the data.

5.  **Results Table (Editable)**: The largest section at the bottom is an editable table. It shows a header row with columns like "ID", "Col1", "Col2", "...", and "Edit". Subsequent rows contain data, with an "[Edit]" button in the last column, suggesting inline editing capabilities for each record. The table supports horizontal and vertical scrolling when content overflows the visible area, and individual columns have a maximum width of approximately 50 characters with overflow content truncated using ellipsis.

The overall layout is clean and functional, designed to provide comprehensive filtering, display customization, and data editing features within a single component.

### Column Width and Overflow Handling
- Individual columns in the results table should have minimal padding
- Columns can expand up to a maximum width of approximately 50 characters
- Content exceeding this width should be truncated with an ellipsis (...)

### Table Scrolling
- The entire results table must be scrollable both vertically and horizontally
- Vertical scrolling is enabled when there are more rows than can fit in the visible area
- Horizontal scrolling is enabled when the total width of columns exceeds the visible area
- Scrollbars should appear automatically when needed

## Technical Details

### Database Integration
- Use SQLAlchemy queries following DatabaseManager patterns
- Leverage existing session management
- Implement efficient querying with selected columns only

### Data Flow
1. User defines filters
2. Component builds SQLAlchemy query
3. DatabaseManager executes query
4. Results displayed in editable table
5. User edits data
6. Changes saved via DatabaseManager

### Error Handling
- Invalid regex patterns
- Database connection issues
- Validation errors on save

## Dependencies
- Flet for UI components
- SQLAlchemy for database operations
- Existing DatabaseManager for session handling
- DpdHeadword model for column definitions

## Future Enhancements
- OR/AND filter combinations
- Saved filter presets
- Export filtered results
- Sorting capabilities