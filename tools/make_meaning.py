
def make_meaning(i):
    if i.meaning_1 == "":
        meaning = i.meaning_2
    else:
        meaning = i.meaning_1
    if i.meaning_lit != "":
        meaning += f"; lit. {i.meaning_lit}"
    return meaning
