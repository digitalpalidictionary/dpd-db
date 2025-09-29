# Specification for Pass1 File Access

## 1. Current State

### 1.1. Overview

The `pass1_add` and `pass1_auto` features both read and write to the same set of JSON files located in the `gui2/data` directory. The files are named dynamically based on the book being processed, e.g., `pass1_auto_dhpa.json`.

This concurrent access by two different parts of the application is causing a race condition, leading to data corruption.

### 1.2. `Pass1AddController`

-   **File Access:** Reads and writes to the JSON files directly.
-   **`load_json()`:** Reads the entire JSON file for a given book into memory.
-   **`remove_word_and_save_json()`:** Reads the file, removes an entry, and writes the entire dictionary back to the file. This is a classic read-modify-write pattern that is not atomic.

### 1.3. `Pass1AutoController`

-   **File Access:** Reads and writes to the JSON files directly.
-   **`load_auto_processed()`:** Reads the entire JSON file for a given book into memory.
-   **`update_auto_processed()`:** Reads the file, adds a new entry, and writes the entire dictionary back to the file. This is also a non-atomic read-modify-write pattern.
-   **Locking:** It uses a `self.locked` flag in an attempt to prevent race conditions, but this lock is not shared with `Pass1AddController` and is therefore ineffective.

### 1.4. The Problem

The core issue is the lack of a shared, atomic mechanism for file access between the two controllers. When both controllers perform a read-modify-write cycle at the same time, they can overwrite each other's changes, leading to data loss.

## 2. Proposed Changes

### 2.1. Overview

To solve the race condition, we will centralize the data and file I/O in the `Pass1AutoController`. This controller will be the "owner" of the `pass1_auto` data, and the `Pass1AddController` will access the data through it. This approach is simpler and more elegant than creating a new file manager class.

### 2.2. `Pass1AutoController`

-   **Data Ownership:** `Pass1AutoController` will be responsible for reading, writing, and holding the `auto_processed_dict` in memory.
-   **Locking:** A `threading.Lock` will be added to `Pass1AutoController` to ensure thread-safe access to the `auto_processed_dict` and the underlying JSON files.
-   **Public Methods:** The controller will expose the following thread-safe methods for accessing the data:
    -   `get_auto_processed_dict(book)`: Returns a copy of the `auto_processed_dict` for the given book.
    -   `remove_word(book, word)`: Removes a word from the `auto_processed_dict` and saves the updated dictionary to the corresponding JSON file.
    -   `add_word(book, word, data)`: Adds a word and its data to the `auto_processed_dict` and saves the file.

### 2.3. `Pass1AddController`

-   **Data Access:** `Pass1AddController` will no longer access the JSON files directly. Instead, it will get a reference to the `Pass1AutoController` instance (likely via the `ToolKit`) and use its public methods to access and modify the data.
-   **Refactoring:**
    -   `load_json()` will be replaced with a call to `pass1_auto_controller.get_auto_processed_dict(book)`.
    -   `remove_word_and_save_json()` will be replaced with a call to `pass1_auto_controller.remove_word(book, word)`.

### 2.4. `ToolKit`

-   The `Pass1AutoController` instance will be created and managed within the `ToolKit` to ensure a single, shared instance is available to all parts of the application.

### 2.5. Benefits

-   **Simplicity and Elegance:** This solution is simpler and more elegant as it avoids the creation of a new class and establishes a clear data ownership model.
-   **Race Condition Solved:** The `threading.Lock` in `Pass1AutoController` will ensure that all access to the shared data is thread-safe, preventing race conditions and data corruption.
-   **Centralized Logic:** All logic for managing the `pass1_auto` data will be centralized in `Pass1AutoController`, making the code easier to understand and maintain.
