---
name: dpd-database-query
description: Query the Digital Pāḷi Dictionary database to find words, roots, definitions, and related information
tags: [dpd, pali, database, sql, sqlalchemy]
version: 1.0.0
author: DPD Team
dependencies: []
---
# DPD Database Query

## When to use this skill
Use this skill when you need to query the Digital Pāḷi Dictionary database to find specific words, roots, definitions, grammatical information, or related data. This skill is particularly useful when working with the DPD database models and performing data analysis or verification tasks.

## Instructions
1. Import the necessary SQLAlchemy models from `db.models`
2. Establish a database session using the existing DPD database connection
3. Construct queries using SQLAlchemy ORM methods
4. Execute the query and process the results appropriately
5. Close the database session when done

## Examples

### Basic word lookup:
```python
from db.models import DpdHeadword
from db.db_helpers import get_db_session

session = get_db_session()
word = session.query(DpdHeadword).filter(DpdHeadword.lemma_1 == "dhamma").first()
if word:
    print(f"Definition: {word.definition}")
session.close()
```

### Root word lookup:
```python
from db.models import DpdRoot
session = get_db_session()
root = session.query(DpdRoot).filter(DpdRoot.root == "√kar").first()
if root:
    print(f"Root meaning: {root.root_meaning}")
session.close()
```

### Advanced query with relationships:
```python
from db.models import DpdHeadword, DpdRoot
from sqlalchemy.orm import joinedload

session = get_db_session()
words_with_root = session.query(DpdHeadword).options(joinedload(DpdHeadword.rt)).filter(DpdRoot.root == "√kar").all()
for word in words_with_root:
    print(f"Word: {word.lemma_1}, Meaning: {word.meaning}, Root: {word.rt.root_meaning if word.rt else 'N/A'}")
session.close()
```

### Query with multiple conditions:
```python
from db.models import DpdHeadword
session = get_db_session()
results = session.query(DpdHeadword).filter(
    DpdHeadword.pos.like('%noun%'),
    DpdHeadword.meaning.contains('Buddha')
).all()
for word in results:
    print(f"Word: {word.lemma_1}, Meaning: {word.meaning}")
session.close()
```

## Best Practices
- Always close database sessions after use to prevent connection leaks
- Use SQLAlchemy's ORM methods rather than raw SQL when possible for consistency
- Leverage the existing `get_db_session()` helper function
- Use appropriate filters to limit query results for performance
- Handle cases where queries return no results
- Use eager loading with `joinedload` when accessing related objects to avoid N+1 queries
- Follow the existing code style and patterns used in the DPD codebase
- Remember to import the correct model classes from `db.models`
