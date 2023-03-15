import re
from tools.pos import INDECLINEABLES

def add_stem_pattern(values, window):
    pos = values["pos"]
    grammar = values["grammar"]
    pali_1 = values["pali_1"]
    pali_1_clean = re.sub(r"\s\d.*$", "", pali_1)

    if pos == "adj":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a adj")
        if pali_1_clean.endswith("ī"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ī adj")
        if pali_1_clean.endswith("ant"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("ant adj")
        if pali_1_clean.endswith("u"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("u adj")
        if pali_1_clean.endswith("i"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("i adj")
        if pali_1_clean.endswith("ū"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ū adj")
        if pali_1_clean.endswith("aka"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("aka adj")
    
    elif pos == "masc":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a masc")
        if pali_1_clean.endswith("ī"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ī masc")
        if pali_1_clean.endswith("i"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("i masc")
        if pali_1_clean.endswith("u"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("u masc")
        if pali_1_clean.endswith("ar"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ar masc")
        if pali_1_clean.endswith("as"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("as masc")
        if pali_1_clean.endswith("ū"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ū masc")
        if pali_1_clean.endswith("ant"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("ant masc")

    elif pos == "fem":
        if pali_1_clean.endswith("ā"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ā fem")
        if pali_1_clean.endswith("i"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("i fem")
        if pali_1_clean.endswith("ī"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ī fem")
        if pali_1_clean.endswith("u"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("u fem")
        if pali_1_clean.endswith("ar"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ar fem")
        if pali_1_clean.endswith("ū"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ū fem")

    elif pos == "nt":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a nt")
        if pali_1_clean.endswith("u"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("u nt")
        if pali_1_clean.endswith("i"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("i nt")

    elif pos == "card":
        if "x pl" in grammar:
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a1 card")
        if "nt sg" in grammar:
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a2 card")
        if pali_1_clean.endswith("i"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("i card")
        if pali_1_clean.endswith("koṭi"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("i2 card")
        if pali_1_clean.endswith("ā"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ā card")

    elif pos == "ordin":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a ordin")

    elif pos == "pp":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a pp")

    elif pos == "prp":
        if pali_1_clean.endswith("anta"):
            window["stem"].update(pali_1_clean[:-4])
            window["pattern"].update("anta prp")
        if pali_1_clean.endswith("enta"):
            window["stem"].update(pali_1_clean[:-4])
            window["pattern"].update("enta prp")
        if pali_1_clean.endswith("onta"):
            window["stem"].update(pali_1_clean[:-4])
            window["pattern"].update("onta prp")
        if pali_1_clean.endswith("māna"):
            window["stem"].update(pali_1_clean[:-4])
            window["pattern"].update("māna prp")
        elif pali_1_clean.endswith("āna"):
            window["stem"].update(pali_1_clean[:-4])
            window["pattern"].update("āna prp")

    elif pos == "ptp":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a ptp")

    elif pos == "pron":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a pron")

    elif pos == "pr":
        if pali_1_clean.endswith("ati"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("ati pr")
        if pali_1_clean.endswith("eti"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("eti pr")
        if pali_1_clean.endswith("oti"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("oti pr")
        if pali_1_clean.endswith("āti"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("āti pr")

    elif pos == "aor":
        if pali_1_clean.endswith("i"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("i aor")
        if pali_1_clean.endswith("esi"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("esi aor")
        if pali_1_clean.endswith("āsi"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("āsi aor")

    elif pos == "perf":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a perf")

    elif pos == "imperf":
        if pali_1_clean.endswith("ā"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ā imperf")

    elif pos in INDECLINEABLES:
        window["stem"].update("-")
        window["pattern"].update("")

# !!! add all the plural forms !!!
