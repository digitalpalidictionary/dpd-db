def dedupe_list(list) -> list:
    """Return a list with all duplicates removed,
    while maintaining the correct order."""

    dict = {}
    for i in list:
        dict[i] = None
    return [key for key in dict.keys()]
