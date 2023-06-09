
def db_search_string(list: list) -> str:
    """Input a list and return a regex search string for db brower."""
    return f"/^({'|'.join(list)})$/"