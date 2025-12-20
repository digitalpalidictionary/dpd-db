# Developer Quick Start Guide

Welcome to the Digital Pāḷi Dictionary (DPD) developer guide. This page will help you get started with using the DPD database and codebase for your own projects.

## Getting Started

### Prerequisites

1. **Database**: Download the latest `dpd.db.tar.bz2` from the [dpd-db releases page](https://github.com/digitalPāḷidictionary/dpd-db/releases){target="_blank"}
2. **Python Environment**: Install [uv](https://astral.sh/uv/install){target="_blank"} for dependency management
3. **Dependencies**: Run `uv sync` to install all required dependencies

### Basic Database Usage

The DPD database is a SQLite database with comprehensive Pāḷi grammatical data. Here's how to get started:

```python
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup

# Connect to the database
db_session = get_db_session(Path("dpd.db"))

# Query headwords
headwords = db_session.query(DpdHeadword).filter(DpdHeadword.pos == "nt").all()

for i in headwords:
    print(i.lemma_1, i.pos, i.meaning_combo)

# Close the session
db_session.close()
```

## Key Database Tables

### `dpd_headwords` Table

This is the main table containing all Pāḷi headwords with comprehensive grammatical information. See the [full table documentation](dpd_headwords_table.md) for all available columns.

### `lookup` Table

The lookup table contains inflected forms and their mappings to headwords. This is essential for finding the base form of any inflected Pāḷi word.

## Common Use Cases

### 1. Finding Headwords from Inflected Forms

To find the base headword(s) for any inflected Pāḷi word:

```python
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup

# Connect to the database
db_session = get_db_session(Path("dpd.db"))

# Find exact matching word in the lookup table
lookup_results = (
    db_session.query(Lookup).filter(Lookup.lookup_key == "dhammassa").first()
)

if lookup_results:
    # Unpack the headword ids from the results
    headword_ids = lookup_results.headwords_unpack

    # Lookup those headword ids in `dpd_headwords` table
    headwords = (
        db_session.query(DpdHeadword).filter(DpdHeadword.id.in_(headword_ids)).all()
    )

    # Print the headwords, pos and meaning
    for i in headwords:
        print(f"{i.lemma_1} {i.pos}: {i.meaning_combo}")

```

### 2. Accessing Grammar Information

Grammar data is available directly from the lookup table. Using the same method you can also unpack the data for `deconstructor`, `variant`, `epd`, etc.

```python
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import Lookup

# Connect to the database
db_session = get_db_session(Path("dpd.db"))

# Get Lookup table information for an inflected word
grammar_data = db_session.query(Lookup).filter(Lookup.lookup_key == "dhammassa").first()

if grammar_data:
    # Unpack the grammar data which is stored as a JSON list
    grammar_data_unpack = grammar_data.grammar_unpack

    # Grammar is returned as a list of lists: [[headword, part_of_speech, grammar], ...]
    for g in grammar_data_unpack:
        print(g)
```

## Tips and Best Practices

1. **Use AI for Codebase Navigation**: The DPD codebase is complex with many interdependencies. Use AI tools to trace dependencies and understand the architecture.

2. **Start with Existing Exporters**: Before building your own solution, check existing exporters in the `exporter/` directory.

3. **Leverage Virtual Columns**: The `DpdHeadword` model includes many virtual properties that provide computed data (e.g., `lemma_clean`, `inflections_list`).

4. **Database Relationships**: Use the built-in relationships to access related data:
   - `.rt` for root information
   - `.fr` for family roots
   - `.fw` for family words
    - etc.

## Resources

- [Full DPD Headwords Table Documentation](dpd_headwords_table.md){target="_blank"}
- [Using the DB Guide](use_db.md){target="_blank"}
- [Project Folder Structure](project_folder_structure.md){target="_blank"}
- [GitHub Repository](https://github.com/digitalPāḷidictionary/dpd-db){target="_blank"}

## Need Help?

If you have questions that an LLM can't answer, don't hesitate to reach out via the [contact page](../contact.md). We're happy to help with integrating the DPD database into your application. 
