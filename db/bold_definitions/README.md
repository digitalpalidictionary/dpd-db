# Bold Definitions Extraction

This module extracts bolded words and their accompanying commentary from the CST (Chaṭṭha Saṅgāyana Tipitaka) XML corpus. These extractions provide a dictionary-like view of how words are defined and used within the Pāḷi commentaries and sub-commentaries.

## Features

- **End-of-Sentence Capture**: Correctly identifies and extracts bold definitions even when they appear at the very end of a paragraph or sentence.
- **Tag Splitting**: Automatically detects and splits bold tags that contain multiple distinct definitions (e.g., `<hi>word1. word2</hi>`) into separate searchable entries.
- **Context Awareness**: Dynamically tracks the Nikāya, Book, Title, and Subhead for every extracted definition, supporting both `div`-based and flat XML structures.
- **Robust Cleaning**: Refines commentary snippets to remove noise while preserving the essential context of the definition.

## Core Scripts

- `extract_bold_definitions.py`: The main extraction engine. It parses the entire CST XML corpus and generates `bold_definitions.json` and `bold_definitions.tsv`.
- `update_bold_definitions_db.py`: Clears the `bold_definitions` table in the DPD database and imports the latest extracted data from the TSV file.
- `search_bold_definitions.py`: A CLI tool for searching the extracted definitions using plain text or regular expressions.
- `functions.py`: Contains the data models (`BoldDefinitionEntry`, `Context`), context-tracking logic, and text cleaning utilities.

## Data Structures

The extraction produces entries with the following fields:
- `file_name`: The source CST XML file.
- `ref_code`: The short reference code for the text (e.g., `DNa`, `VINt`).
- `nikaya`, `book`, `title`, `subhead`: The hierarchical context of the definition.
- `bold`: The bolded headword/phrase.
- `bold_end`: The immediate suffix or punctuation following the bold tag (e.g., `ti`, `nti`, `.`).
- `commentary`: The surrounding sentence or paragraph providing the definition.

## Usage

### 1. Extract Data
To run the full extraction process:
```bash
uv run python db/bold_definitions/extract_bold_definitions.py
```

### 2. Update Database
To import the extracted data into `dpd.db`:
```bash
uv run python db/bold_definitions/update_bold_definitions_db.py
```

### 3. Search Definitions
To search the database via CLI:
```bash
uv run python db/bold_definitions/search_bold_definitions.py
```