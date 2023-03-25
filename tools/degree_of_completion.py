def degree_of_completion(i):
    """find a word's degree of completion and gray html ✓~✗"""
    if i.meaning_1:
        if i.example_1:
            return "<span class='gray'>✓</span>"
        return "<span class='gray'>~</span>"
    return "<span class='gray'>✗</span>"
