import re

def map_pos_to_dpd(source_pos: str, headword: str, mapping_dict: dict) -> str:
    """Map source POS to DPD POS."""
    pos = source_pos.strip().lower()

    if " " in headword:
        return "idiom"

    pos_no_brackets = pos.replace("(", "").replace(")", "").replace("[", "").replace("]", "")
    pos_clean = pos_no_brackets.replace(".", "").replace(",", "").replace(" ", "")

    if pos == "pr. 3 sg.":
        return "pr"

    if "mfn" in pos_clean:
        return "adj"

    if pos_clean == "m" or pos.startswith("m."):
        return "masc"
    if pos_clean == "f" or pos.startswith("f."):
        return "fem"
    if pos_clean in ["n", "nt"] or pos.startswith("n.") or pos.startswith("nt."):
        return "nt"

    if re.search(r"tvā(na)?$", headword.lower()):
        return "abs"

    if re.search(r"tuṃ$", headword.lower()):
        return "inf"

    if re.search(r"an[iī]ya$", headword.lower()):
        return "ptp"
    
    if re.search(r"eyya$", headword.lower()) and "mfn" in pos_clean:
        return "ptp"

    if re.search(r"māna$", headword.lower()):
        return "prp"
    if re.search(r"(at|anta)$", headword.lower()) and "mfn" in pos_clean:
        return "prp"

    if re.search(r"(ta|ita|na)$", headword.lower()) and "mfn" in pos_clean:
        return "pp"

    if re.search(r"ar$", headword.lower()):
        return "masc"

    return mapping_dict.get(pos_clean, pos)
