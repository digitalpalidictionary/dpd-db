# gui/auto_suggest/

## Purpose & Rationale
Capturing lexicographical data is a meticulous and error-prone task. The `auto_suggest/` directory exists to solve the problem of data entry fatigue and inconsistency by providing intelligent, context-aware suggestions for editors. Its rationale is to surface patterns from existing database entries (and optionally AI models) to predict the most likely values for fields like grammar, roots, and meanings.

## Architectural Logic
This subsystem follows a "Contextual Pattern Matching" architecture:
1.  **Context Detection:** `AutoSuggestData` analyzes the current word being edited to determine its "type" (e.g., whether it has a root, is a compound, or belongs to a word family).
2.  **Data Harvesting:** It queries the database for "complete" entries that share the same characteristics (e.g., same root or same compound components).
3.  **Suggestion Generation:** It identifies commonalities among these complete entries to provide a list of highly probable suggestions.
4.  **AI Integration:** Optionally utilizes external AI models (via `google.genai`) to suggest meanings or structural breakdowns based on the current context.

## Relationships & Data Flow
- **Source:** Heavily queries the `DpdHeadword` table in **db/**.
- **Consumption:** Integrated directly into the **gui/** event loop to provide real-time dropdowns or field pre-fills for the editor.
- **Feedback Loop:** As more "complete" data is added, the auto-suggestion logic becomes increasingly accurate.

## Interface
This is an internal utility for the GUI. Developers can test the suggestion logic independently by instantiating the `AutoSuggestData` class with a specific headword ID.
