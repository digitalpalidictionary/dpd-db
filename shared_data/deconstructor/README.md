# shared_data/deconstructor/

## Purpose & Rationale
Compound word deconstruction is one of the project's most complex tasks. The `deconstructor/` directory exists to provide the "Human Intelligence" layer that guides the automated deconstruction engines. Its rationale is to store manually verified rules, exceptions, and corrections that prevent the algorithms from making logical errors when splitting Pāḷi words.

## Architectural Logic
This directory follows a "Heuristic Override and Rulebase" pattern:
1.  **Rules (`sandhi_rules.tsv`):** Defines the phonetic and structural rules used to split compounds.
2.  **Overrides (`manual_corrections.tsv`):** Stores explicit splits for words where the automated logic fails.
3.  **Blacklists (`exceptions.tsv`):** Prevents the deconstructor from splitting words that should remain whole.
4.  **Verification (`checked.csv`):** Tracks which words have been manually reviewed by a lexicographer.

## Relationships & Data Flow
- **Consumption:** These files are the primary input for the high-performance **go_modules/deconstructor/** subsystem.
- **Feedback:** As the Go-based engine identifies new patterns or errors, they are added to these TSVs to improve the next build cycle.

## Interface
Managed primarily via manual TSV edits in response to deconstruction error reports.
