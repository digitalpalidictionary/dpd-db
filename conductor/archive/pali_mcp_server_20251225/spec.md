# Pāḷi MCP Server Specification

## Overview
A Python-based Model Context Protocol (MCP) server that provides AI agents with structured access to the Digital Pāḷi Dictionary (DPD). The server exposes tools to analyze Pāḷi sentences by tokenizing them and retrieving high-precision grammatical and semantic data from the DPD SQLite database.

## Functional Requirements

### 1. `get_grammatical_details` Tool
- **Input:** A Pāḷi sentence (string).
- **Process:**
    1.  **Tokenization:** Remove standard punctuation and split by whitespace.
    2.  **Normalization:** Convert all tokens to lowercase for the initial lookup.
    3.  **Lookup:**
        - For each token, query the `lookup` table in `dpd.db`.
        - Retrieve `headwords` (JSON list of IDs) from the `lookup` entry.
    4.  **Headword Retrieval:**
        - For each headword ID found, query the `dpd_headwords` table.
        - Extract specific fields: `id`, `lemma_1`, `pos`, `grammar`, `meaning_combo`, `family_root`.
- **Output:** A structured JSON object containing the analysis for each word in the sentence.
    - Successfully found words include their grammatical details.
    - Words not found are included in the results with a `status: "not_found"` flag.

### 2. Database Integration
- Use the existing `dpd.db` SQLite database.
- Utilize SQLAlchemy models defined in `db/models.py` (specifically `DpdHeadword`).
- Leverage existing helper functions from `db/db_helpers.py` and logic from `exporter/webapp/main.py`.

## Non-Functional Requirements
- **Performance:** Database queries must be optimized for interactive response times.
- **Reliability:** Graceful handling of malformed input and empty strings.
- **Maintainability:** Use the official `mcp` Python SDK and adhere to existing project standards (Ruff, type hints).

## Acceptance Criteria
- [ ] An AI agent can call `get_grammatical_details` with a Pāḷi sentence.
- [ ] The tool returns a JSON structure containing correct data for words present in DPD.
- [ ] Punctuation is stripped and lowercase normalization is applied.
- [ ] Missing words are explicitly marked as `not_found`.
- [ ] No sys.path hacks or manual directory traversal; use established project patterns.

## Out of Scope (First Iteration)
- Compound deconstruction for words not found in the lookup table.
- Sutta example fetching or audio integration.
- Built-in prompt formatting (the server provides raw data only).
