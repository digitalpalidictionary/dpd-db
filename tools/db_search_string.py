"""Returns a regex string that can be used for searching in DB browser or GUI."""


def db_search_string(
    words: list | set, start_end: bool = True, gui: bool = False
) -> str:
    """Input a list or set and return a regex search string for db browser or GUI."""
    joined = "|".join(str(i) for i in words)
    if gui:
        return f"^({joined})$"
    if start_end:
        return f"/^({joined})$/"
    else:
        return f"/\\b({joined})\\b/"
