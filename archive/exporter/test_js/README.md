# exporter/test_js/

## Purpose & Rationale
`test_js/` is a specialized debugging environment for the project's frontend logic. Its rationale is to provide a way to test the complex JavaScript components (lazy loading, templating, button interactions) used in GoldenDict and MDict within a standard browser environment. It solves the problem of "blindly" debugging JS code that is typically only executed inside dictionary shell apps.

## Architectural Logic
This directory follows a "Mock Integration Test" pattern:
1.  **Harness:** `test.html` mimics the structure of a real GoldenDict dictionary entry.
2.  **Asset Loading:** It references the real CSS and JS files from the `exporter/goldendict/` directory.
3.  **Simulation:** It contains mock data variables (e.g., `rootdata_car_1`) to simulate how data is injected into the entry at runtime.
4.  **Verification:** It allows developers to use browser developer tools (Inspect, Console) to verify that the project's custom lazy-loading logic and UI components are functioning as expected.

## Relationships & Data Flow
- **Input:** Relies on the development versions of assets in **exporter/goldendict/javascript/**.
- **Consumption:** Used exclusively by developers during the development of new interactive dictionary features.

## Interface
- **Debug:** Open `exporter/test_js/test.html` in a web browser to test interactive features and view console output.
