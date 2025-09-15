# GUI2 Tests Tab Specification

## Overview
This document specifies the functionality, behavior, and implementation details of the Tests Tab in the GUI2 application. The Tests Tab provides a comprehensive interface for running database tests, managing test definitions, and viewing test results with integration to the FilterComponent for data display and manipulation.

## Expected Behavior

### Core Functionality
1. **Test Execution**: Users can run a suite of internal database tests with progress tracking
2. **Test Management**: Users can add, update, and delete test definitions
3. **Result Visualization**: Test failures are displayed using the FilterComponent with customizable filters
4. **Exception Handling**: Users can manage exceptions for test failures
5. **Query Management**: Users can copy database queries for further analysis

### User Workflow
1. User clicks "Run Tests" to initiate the test suite
2. Progress bar indicates test execution status
3. For each failing test, details are displayed and results shown in FilterComponent
4. User can add exceptions, update tests, or navigate between test results
5. User can stop test execution at any time

## Event Handlers

### Primary Event Handlers

#### `handle_run_tests_clicked`
- **Trigger**: Click on "Run Tests" button
- **Behavior**:
  - Disables run button and enables stop button
  - Initializes progress bar
  - Loads database entries and test definitions
  - Performs integrity check on tests
  - Executes tests sequentially with progress updates
  - For each failing test:
    - Populates test definition fields
    - Updates exceptions dropdown with failure IDs
    - Creates FilterComponent with failure data
    - Updates query field
  - Re-enables run button and hides progress bar upon completion

#### `handle_stop_tests_clicked`
- **Trigger**: Click on "Stop Tests" button
- **Behavior**:
  - Immediately stops test execution by setting stop flag and calling finalize
  - Re-enables run button, disables stop button
  - Hides progress bar
  - Resets generator, db entries, and tests list
  - Clears all fields in the view, including the FilterComponent/datatable by setting it to None
  - Shows "Tests stopped" snackbar

#### `handle_edit_tests_clicked`
- **Trigger**: Click on "Edit Tests" button
- **Behavior**:
  - Opens the tests definition file in LibreOffice or default editor

#### `handle_next_clicked`
- **Trigger**: Click on "Next" button
- **Behavior**:
  - Clears all fields in preparation for next test

#### `handle_test_update`
- **Trigger**: Click on "Update Tests" button
- **Behavior**:
  - Checks if a current test is active (from ongoing test run)
  - Reads test_name, iterations, all 6 search criteria, error_column, display fields, and exceptions (comma-separated IDs from TextField, parsed to list[int])
  - Updates the corresponding InternalTestRow in the test manager's list
  - Saves the updated tests to file via DbTestManager
  - Shows success feedback via snackbar; warns if exception parsing fails

#### `handle_add_new_test`
- **Trigger**: Click on "Add New Test" button
- **Behavior**:
  - Reads test fields from view
  - Creates new test definition
  - Adds test to test manager list
  - Saves updated tests to file
  - Clears view fields

#### `handle_delete_test`
- **Trigger**: Click on "Delete Test" button
- **Behavior**:
  - Removes current test from test manager list
  - Saves updated tests to file
  - Clears view fields

#### `handle_add_exception_button`
- **Trigger**: Click on "Add Exception" button
- **Behavior**:
  - Gets selected ID from dropdown
  - Adds ID to current test exceptions
  - Removes ID from dropdown options
  - Updates view

#### `handle_test_db_query_copy`
- **Trigger**: Click on copy query button
- **Behavior**:
  - Copies query text from input field to clipboard
  - Shows confirmation snackbar

#### `handle_next_test_clicked`
- **Trigger**: Click on "Next" button in test navigation
- **Behavior**:
  - Clears all fields in the view

## FilterComponent Integration

### Data Flow
1. **Test Failure Detection**: When a test fails, failure IDs are collected
2. **Filter Creation**: Data filters are created using failure IDs with regex patterns
3. **Display Configuration**: Display filters are created from test display settings
4. **Component Instantiation**: FilterComponent is instantiated with filters and limit
5. **View Integration**: FilterComponent is displayed in the results container

### Configuration Parameters
- **Data Filters**: List of tuples containing column names and regex patterns
- **Display Filters**: List of column names to display in results
- **Limit**: Maximum number of results to display

### Result Display
- FilterComponent displays test failures in an editable data table
- Users can modify data directly in the table
- Changes can be saved back to the database
- Row selection copies display values to clipboard

## Generator-Based Stepping Implementation

### Test Execution Flow
- Test execution is driven by a generator that yields test definitions one by one
- The `next()` function is used to advance to the next test in the sequence
- Each test is processed individually, and the UI is updated to reflect the current test's status
- For failing tests, advancement to the next test requires explicit user interaction (e.g., clicking a "Next" button)
- For passing tests, the system automatically advances to the next test

### UI Updates and User Interaction
- When a test is running, the UI displays the test name and other relevant information
- For failing tests, the results are displayed in the FilterComponent, and the user can interact with the data
- For passing tests, a brief success message is shown before automatically advancing to the next test
- The "Next" button is used to advance to the next test in the sequence for failing tests
- The "Stop Tests" button can be used to terminate the test execution at any point

### State Management
- The controller maintains the state of the current test generator
- A flag is used to track whether test execution has been stopped by the user
- The UI is updated to reflect the current state of test execution (running, stopped, completed)

## Test Management Features

### Test Definition Structure
Tests are defined using `InternalTestRow` objects with the following properties:
- `test_name`: Name of the test
- `iterations`: Number of iterations to display
- `search_column_*`: Column names for search criteria (up to 6)
- `search_sign_*`: Search operators (equals, contains, etc.)
- `search_string_*`: Search values
- `error_column`: Column to check for errors
- `exceptions`: List of exception IDs
- `display_*`: Columns to display in results (up to 3)

### CRUD Operations
1. **Create**: Add new test definitions through the "Add New Test" button
2. **Read**: Load existing tests from file on test execution
3. **Update**: Modify existing test definitions with "Update Tests" button
4. **Delete**: Remove test definitions with "Delete Test" button

### Data Persistence
- Tests are saved to and loaded from files using the `DbTestManager`
- All changes are immediately persisted to storage
- File-based storage allows for external editing

## Exception Handling

### Exception Workflow
1. **Detection**: Failed test IDs are identified during test execution
2. **Filtering**: IDs already in exceptions list are filtered out
3. **Presentation**: Current exceptions shown as comma-separated string in TextField; new failures available for adding via separate dropdown
4. **Management**: Users can edit exceptions in TextField or add via "Add Exception" during run

### Data Validation
- Exception IDs are validated before addition
- Only valid IDs from current test failures can be added
- Dropdown options are dynamically updated when exceptions are added

### Error States
- Database loading errors are displayed in the test name field
- Test integrity failures show the first failing test
- FilterComponent handles regex validation and displays errors

## Query Copy Functionality

### Implementation
- Query text is generated based on current test failures
- Uses regex pattern matching for ID filtering
- Copy functionality uses `pyperclip` library for clipboard operations
- Confirmation is shown through Flet Snackbar

### User Experience
- Single click operation to copy query
- Visual confirmation of copy operation
- Query format suitable for direct database use

## UI Components

### Input Fields
- Test name and iteration count
- Search criteria (column, operator, value) for up to 6 conditions
- Display column selectors (up to 3)
- Error column specification
- Exceptions as editable TextField with comma-separated IDs

### Action Buttons
- Run/Stop test execution
- Edit tests in external editor
- Test management (Add, Update, Delete)
- Exception handling
- Navigation controls
- Query copy

### Display Elements
- Progress bar for test execution
- Results summary (displaying X of Y results)
- FilterComponent for result visualization
- Test navigation indicators

## Integration Points

### Database Manager
- Direct access to `DpdHeadword` database entries
- Test execution runs queries against all database entries
- FilterComponent provides database update capabilities

### Toolkit
- Provides access to database manager and test manager
- Centralizes application state and resources
- Handles database persistence operations

### External Systems
- LibreOffice or default editor for test file editing
- Clipboard for query copying
- File system for test definition storage

## Error Handling

### Recoverable Errors
- Database loading failures show error in UI and allow retry
- Test integrity failures highlight problematic tests
- FilterComponent regex errors display validation messages

### Non-Recoverable Errors
- System exceptions during test execution stop the test run
- Database save failures rollback changes and show error messages
- File access errors for test definitions show appropriate messages

## Performance Considerations

### Memory Management
- Test results are limited by iteration count to prevent memory issues
- FilterComponent uses virtualized scrolling for large result sets
- Database queries are limited to prevent excessive data loading

### Responsiveness
- Generator-based execution ensures UI remains responsive during test execution
- Progress updates provide user feedback during long operations
- Asynchronous operations use Flet's built-in mechanisms

## Future Extensibility

### Planned Enhancements
- Enhanced test definition editor within the application
- Test result history and comparison
- Export functionality for test results
- Advanced filtering options in FilterComponent
- Test scheduling and automation features

### Extension Points
- Additional test types beyond database validation
- Integration with external test frameworks
- Custom validation rules for specific test scenarios
- Advanced reporting and visualization options