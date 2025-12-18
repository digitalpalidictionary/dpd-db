"""Returns a regex string that can be used for searching in DB browser."""


def db_search_string(list: list | set, start_end=True) -> str:
    """Input a list or set and return a regex search string for db brower."""
    new_list = []
    for i in list:
        new_list.append(str(i))
    if start_end:
        return f"/^({'|'.join(new_list)})$/"
    else:
        return f"/\\b({'|'.join(new_list)})\\b/"
