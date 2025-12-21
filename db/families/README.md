# db/families/

## Purpose & Rationale
The `families/` directory manages the grouping of Pāḷi words into logical and etymological clusters. By organizing words into "families," the project provides deep context for each headword, allowing users to see related terms, common roots, and thematic sets. This subsystem solves the problem of word isolation by making relationships explicit.

## Architectural Logic
This directory follows a "Family Grouping" pattern, with specialized logic for different relationship types:
- **Root Families (`family_root.py`):** Groups all headwords derived from the same Pāḷi root. It generates HTML tables summarizing these relationships.
- **Word Families (`family_word.py`):** Clusters words that are etymologically related but might not share a simple root.
- **Compound Families (`family_compound.py`):** Organizes compound words by their components.
- **Idiom Families (`family_idiom.py`):** Groupings based on common idiomatic usage.
- **Set Families (`family_set.py`):** Thematic groupings (e.g., "birds," "parts of the body").
- **Matrix Logic (`root_matrix.py`):** Generates complex visualizations of how roots evolve into diverse Pāḷi terms.

## Relationships & Data Flow
- **Input:** Aggregates and filters data from the primary `DpdHeadword` and `DpdRoot` tables.
- **Output:** Populates specialized "family" tables in the database (e.g., `family_root`, `family_compound`) and generates pre-rendered HTML snippets.
- **Consumption:** The **GUI** uses these families for cross-referencing, and the **Exporters** package the generated HTML into the final dictionary products.

## Interface
Each family type can be updated individually:
- `uv run python db/families/family_root.py`
- `uv run python db/families/family_word.py`
- (etc.)
