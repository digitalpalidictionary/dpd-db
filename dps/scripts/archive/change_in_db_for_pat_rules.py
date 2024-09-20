#!/usr/bin/env python3

"""
The filter_and_update function updates the DpdHeadword database entries. For entries where lemma_1 ends with 'sikkhāpada' and meaning_2 is empty, it sets a new family set and updates meaning_2 based on patterns in meaning_1.
"""


from db.models import DpdHeadword
from tools.paths import ProjectPaths
from db.db_helpers import get_db_session
from rich.console import Console
import re

console = Console()


def filter_and_update():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # Find the words that match the filter criteria
    words_to_update = db_session.query(DpdHeadword).filter(
        DpdHeadword.lemma_1.endswith('sikkhāpada'),
        DpdHeadword.meaning_2 == ""
    ).all()

    for word in words_to_update:
        word.family_set= "bhikkhupātimokkha rules"

        if word.meaning_1:
            if m := re.search(r'Pācittiya (\d+)', word.meaning_1):
                word.meaning_2 = f"PC{m.group(1)}"
            elif m := re.search(r'Saṅghādisesa (\d+)', word.meaning_1):
                word.meaning_2 = f"SA{m.group(1)}"
            elif m := re.search(r'Pāṭidesanīya (\d+)', word.meaning_1):
                word.meaning_2 = f"PD{m.group(1)}"
            elif m := re.search(r'Sekhiya (\d+)', word.meaning_1):
                word.meaning_2 = f"SE{m.group(1)}"
            elif m := re.search(r'Nissaggiya (\d+)', word.meaning_1):
                word.meaning_2 = f"NP{m.group(1)}"  

        print(f"id: {word.id}, {word.family_set}, {word.meaning_2}")


    # db_session.commit()


# !To use the function:
# filter_and_update()

"""
This program contains two main functions:

    update_from_text_file: This function processes a word's lemma_1 field by removing the suffix "sikkhāpada". It then searches for this processed word in a given text file to determine its corresponding rule number.

    filter_and_update_from_file: This function first reads the content of a specified text file. It then filters words from the database where the family_set is set to "bhikkhupātimokkha rules". For each of these words, it calls update_from_text_file to identify and assign the appropriate rule number to the meaning_2 field of the word.

In summary, the program identifies words associated with "bhikkhupātimokkha rules", extracts the relevant rule numbers from a text file, and updates these rule numbers in the database.
"""


def update_from_text_file(word, text_content):
    """
    Given a word object, this function processes its lemma_2 and search for its corresponding rule in the provided text_content.
    It then returns the found rule number.
    """
    # Process the lemma_2 field
    rule_name = word.lemma_2

    # Create a regular expression pattern to search for the rule name and its number
    pattern = re.compile(rf"{rule_name} (\w+\d+)", re.IGNORECASE)

    match = pattern.search(text_content)
    if match:
        return match.group(1)  # return the rule number
    else:
        return None




def filter_and_update_from_file(pth: ProjectPaths):
    # Define the path to your text file
    file_path = "/home/deva/Documents/dpd-db/temp/chattha-sangayana-patimokkhha.txt"

    # Read the content of the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print("First 100 characters of content:", content[:100])  # Just a debug line

    # Initialize a database session
    db_session = get_db_session(pth.dpd_db_path)

    # Find the words that match the filter criteria of having family_set set to "bhikkhupātimokkha rules"
    words_to_update = db_session.query(DpdHeadword).filter(
        DpdHeadword.family_set == "bhikkhupātimokkha rules",
        DpdHeadword.meaning_2 == ""
    ).all()

    print("Number of words found:", len(words_to_update))  # Debug info
    print("First few words:", [word.lemma_2 for word in words_to_update[:5]])  # Debug info


    for word in words_to_update:
        rule_number = update_from_text_file(word, content)
        if rule_number:
            word.meaning_2 = rule_number
            print(f"+Success: lemma_2: {word.lemma_2}, meaning_2: {word.meaning_2}")
        else:
            print(f"Failed: {word.lemma_2}")  # This will let us know which words did not get updated


    # db_session.commit()

# !To use the function:
# filter_and_update_from_file()



def update_family_set_based_on_conditions(pth: ProjectPaths):
    """
    This function will update the `family_set` attribute of `DpdHeadword` objects based on certain conditions.
    
    Args:
    - session: This is the database session, assumed to be an SQLAlchemy session.
    """

    db_session = get_db_session(pth.dpd_db_path)

    # Filtering DpdHeadword objects where family_set is "bhikkhupātimokkha rules" and meaning_2 is empty
    for word in db_session.query(DpdHeadword).filter_by(family_set="bhikkhupātimokkha rules", meaning_2=""):
        word.family_set = ""

        print(f"id: {word.id}, meaning_2 : {word.meaning_2} family_set(new): {word.family_set}")


    # Commit the changes to the database
    # db_session.commit()


# !To use the function:
pth = ProjectPaths()
update_family_set_based_on_conditions(pth)
