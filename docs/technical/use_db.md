# Using the DB

There is a comprehensive database model and lots of pre-existing tools in the repo. To use them:

Clone this repo.

Download **dpd.db.tar.bz2** from [the dpd-db release page](https://github.com/digitalpalidictionary/dpd-db/releases){target="_blank"}, 

Unzip and place the db in the root of the project folder.

Install [uv](https://astral.sh/uv/install){target="_blank"} for your operating system

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install the dependencies with uv

**Minimal dependencies for running database and webapp:** 
```bash
uv sync
```
**Full set of dependencies for running exporters:** 
```bash
uv sync --group tools
```

Here's a quick tutorial how to use the database with Python and SQLAlchemy and the DPD project dependencies, but of course you can use it with your software tools of choice. 


``` py

"""A tutorial demonstrating how to search the DPD database using SQLAlchemy,
and how to make changes and commit them to the database."""

# These are the essential imports needed for database operations
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths

# To access any table, import its corresponding class here
# Other available options include DpdRoot, DbInfo, and Lookup, etc.
from db.models import DpdHeadword

pth = ProjectPaths()
# This establishes a connection to the database - use it once to access the database
db_session = get_db_session(pth.dpd_db_path)

# Example of searching a table using basic filters:
# Find records where part of speech is "adj" and words start with "a"
search_results = (
    db_session.query(DpdHeadword)
    .filter(DpdHeadword.pos == "adj", DpdHeadword.lemma_1.startswith("a"))
    .all()
)
# Note: The results are returned as a list of DpdHeadword class instances

# Loop through the list of search results
for i in search_results:
    # Access any table column using dot notation
    print(f"{'PALI:':<15}{i.lemma_1}")
    # The :<15 format specifier left-justifies the text within 15 characters
    print(f"{'POS:':<15}{i.pos}")

    # Display meaning_2 if meaning_1 is empty
    if i.meaning_1:
        print(f"{'MEANING:':<15}{i.meaning_1}")
    else:
        print(f"{'MEANING:':<15}{i.meaning_2}")

    # Check if there is a root associated with the word
    if i.root_key:
        # This check prevents a NoneType AttributeError when trying to access
        # root information for words without an associated root

        # Access the root table using i.rt.root column names
        print(
            f"{'ROOT':<15}{i.rt.root_clean} {i.rt.root_group} {i.root_sign} ({i.rt.root_meaning})"
        )

    # Import the inflections list which is stored as a CSV-formatted string
    inflections = i.inflections_list

    # Loop through the inflections and print them
    print(f"{'INFLECTIONS:':<15}", end="")
    for inflection in inflections:
        print(f"{inflection}", end=" ")
    print()
    print()

    # You can modify any database information here, for example:
    # if i.pos == "adj":
    #     i.pos = "adjective"

# This would commit any changes to the database - remember there is no undo!
# db_session.commit()

# Always close the database session when you're finished
db_session.close()
```

Alternatively, just download the database and use it with your software tools of choice. 