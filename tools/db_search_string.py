"""Returns a regex string that can be used for searching in DB browser."""


def db_search_string(list: list|set) -> str:
    """Input a list or set and return a regex search string for db brower."""
    new_list = []
    for i in list:
        new_list.append(str(i))
    return f"/^({'|'.join(new_list)})$/"
