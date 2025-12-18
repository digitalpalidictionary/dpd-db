import re


def fuzzy_replace(string: str) -> str:
    string = re.sub("aa|aā|āa|a|ā", "(a|ā|aa|aā|āa)", string)
    string = re.sub("ii|iī|īi|i|ī", "(i|ī|ii|iī|īi)", string)
    string = re.sub("uu|uū|ūu|u|ū", "(u|ū|uu|uū|ūu)", string)
    string = re.sub("kkh|kk|kh|k", "(k|kk|kh|kkh)", string)
    string = re.sub("ggh|gg|gh|g", "(g|gh|gg|ggh)", string)
    string = re.sub("ṅṅ|ññ|ṇṇ|nn|ṅ|ñ|ṇ|n|ṃ", "(ṅ|ñ|ṇ|n|ṅṅ|ññ|ṇṇ|nn|ṃ)", string)
    string = re.sub("cch|cc|ch|c", "(c|ch|cc|cch)", string)
    string = re.sub("jjh|jj|jh|j", "(j|jh|jj|jjh)", string)
    string = re.sub("ṭṭh|tth|ṭṭ|tt|ṭh|th|ṭ|t", "(ṭ|ṭh|ṭṭ|ṭṭh|t|tt|th|tth)", string)
    string = re.sub("ḍḍh|ddh|ḍḍ|dd|ḍh|dh|ḍ|d", "(ḍ|ḍh|ḍḍ|ḍḍh|d|dh|dd|ddh)", string)
    string = re.sub("pph|pp|ph|p", "(p|ph|pp|pph)", string)
    string = re.sub("bbh|bb|bh|b", "(b|bh|bb|bbh)", string)
    string = re.sub("mm|m|ṃ", "(m|mm|ṃ)", string)
    string = re.sub("yy|y", "(y|yy)", string)
    string = re.sub("rr|r", "(r|rr)", string)
    string = re.sub("ll|l|ḷ", "(l|ll|ḷ)", string)
    string = re.sub("vv|v", "(v|vv)", string)
    string = re.sub("ss|s", "(s|ss)", string)
    return string
