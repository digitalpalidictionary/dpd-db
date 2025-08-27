---
description: "Write a comprehensive test suite for a file or function."
argument-hint: "<file_or_function_to_test>"
---

Please write a comprehensive test suite for the specified file or function.

Follow these steps:

1.  **Analyze the Code**:
    *   Read the code of the file or function provided.
    *   Identify its primary purpose, inputs, outputs, and any side effects.
    *   Note any dependencies it has on other parts of the codebase.

2.  **Identify Test Cases**:
    *   **Happy Path**: Test the function with typical, expected inputs.
    *   **Edge Cases**: Test with boundary values (e.g., empty strings, zeros, `None`, large numbers).
    *   **Error Conditions**: Test how the code behaves with invalid inputs (e.g., incorrect data types) and ensure it raises appropriate exceptions.

3.  **Write the Tests**:
    *   Use the `pytest` framework.
    *   Create a new test file, or add to an existing one, in the appropriate `tests/` directory.
    *   Use clear and descriptive names for test functions, like `test_function_name_with_specific_input()`.
    *   Use fixtures for setup and teardown where necessary (e.g., for database connections or temporary files).
    *   Add `@pytest.mark.parametrize` to test multiple scenarios with the same test function efficiently.

4.  **Assertions**:
    *   Use simple `assert` statements.
    *   Ensure each test makes specific and meaningful assertions.

5.  **Review**:
    *   Ensure the tests are easy to read and understand.
    *   Confirm that the tests cover the identified cases and are independent of each other.