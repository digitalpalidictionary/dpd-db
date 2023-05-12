# these are the imports you will always need
from db.get_db_session import get_db_session

# if you want to access any table, import its Class here, other options are PaliRoot, Sandhi, families etc.
from db.models import PaliWord

# this connects to the db, use it once to access the db
db_session = get_db_session("dpd.db")

# this is how to search a table using a basic filter for
# pos == "adj" and words starts with "abh"
search_results = db_session.query(PaliWord).filter(
    PaliWord.pos == "adj", PaliWord.pali_1.startswith("a")).all()
# take note the results are returned as a [list] of PaliWord class instances

# then loop through the list of results
for i in search_results:

    # test if the Russian exists
    if i.ru:

        # now you can access any table column by dot notation
        # :<15 means 'left justify the text by 15 characters'
        print(f"{'PALI:':<15}{i.pali_1}")
        print(f"{'POS:':<15}{i.pos}")

        # show meaning_2 if meaning_1 is empty
        if i.meaning_1 != "":
            print(f"{'MEANING:':<15}{i.meaning_1}")
        else:
            print(f"{'MEANING:':<15}{i.meaning_2}")

        # access the russian table with i.ru
        print(f"{'RUSSIAN:':<15}{i.ru.ru_meaning}")

        # this checks if there's a root
        if i.root_key != "":
            # if you don't do this, you will get a NoneType Attribute Error trying to access root information where there is no root

            # now you can access the root table using i.rt.root column names
            print(f"{'ROOT':<15}{i.rt.root_clean} {i.rt.root_group} {i.root_sign} ({i.rt.root_meaning})")

        # this imports the inflections list which is stored as csv list in the DerivedData table
        inflections = i.dd.inflections_list

        # this loops through the inflections and prints them out
        print(f"{'INFLECTIONS:':<15}", end="")
        for inflection in inflections:
            print(f"{inflection}", end=" ")
        print()
        print()

        # you could edit any information in the db now, for example
        # if i.pos == "adj":
        #     i.pos = "adjective"

# this would commit any changes you make to the db - remember there is no undo!
# db_session.commit()

# and always close the db session once you're done'
db_session.close()
