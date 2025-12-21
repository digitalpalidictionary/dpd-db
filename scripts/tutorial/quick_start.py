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

# Find exact matching word in lookup table
lookup_results = (
    db_session.query(Lookup).filter(Lookup.lookup_key == "dhammassa").first()
)

if lookup_results:
    # Unpack the headword ids from the results
    headword_ids = lookup_results.headwords_unpack

    # Lookup those headword ids in dpd_headwords table
    headwords = (
        db_session.query(DpdHeadword).filter(DpdHeadword.id.in_(headword_ids)).all()
    )

    # Print the headwords
    for i in headwords:
        print(f"{i.lemma_1} {i.pos}: {i.meaning_combo}")


# Get Lookup table information for an inflected word
grammar_data = db_session.query(Lookup).filter(Lookup.lookup_key == "dhammassa").first()

if grammar_data:
    # Unpack the grammar data which is stored as a JSON list
    grammar_data_unpack = grammar_data.grammar_unpack

    # Grammar is returned as a list of lists: [[headword, part_of_speech, grammar], ...]
    for g in grammar_data_unpack:
        print(g)
