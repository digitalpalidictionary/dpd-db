# Specification: AI-Powered Dictionary Proofreading System

## 1. Overview
This system utilizes Google Gemini AI to proofread and correct spelling/grammar in the English meanings of Pāḷi dictionary entries. It operates by extracting data from the `dpd_headwords` table, processing it in batches via the AI API, and saving the results to a structured file for manual review.

## 2. Functional Requirements

### 2.1. Data Extraction
- **Source:** `dpd_headwords` table in the SQLite database.
- **Fields to Extract:** `id`, `lemma_1`, `meaning_1`.
- **Filtering:** Ability to read the database (initially all entries or a subset).

### 2.2. Prompt Compilation & AI Interaction
- **Prompt:** "Correct the spelling and grammar of the following dictionary meanings. Return the result as a JSON list of objects with 'id' and 'meaning_1_corrected' fields. Do not change the meaning, only fix errors."
- **Batching:** Entries grouped into batches (e.g., 50-100) to optimize performance.
- **Client:** Use `tools/ai_gemini_manager.py`.

### 2.3. Output Handling
- **Format:** Structured file (JSON or TSV) containing `id`, `lemma_1`, `meaning_1` (original), and `meaning_1_corrected`.
- **Workflow:** Output is saved for manual review/editing by the user. Automatic database updates are NOT performed.

## 3. Acceptance Criteria
- [ ] Script iterates through `dpd_headwords`.
- [ ] Script sends batched requests to Gemini API.
- [ ] Script saves original and corrected meanings to a file.