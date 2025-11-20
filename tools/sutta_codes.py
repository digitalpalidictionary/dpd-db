""" "Return a list of sutta codes"""

import re

from db.models import SuttaInfo
from tools.pali_sort_key import pali_list_sorter


def generate_range_of_sutta_codes(code_with_dash: str) -> list[str]:
    if "." in code_with_dash:
        # find the base of the code, 'SN12.' in 'SN12.5-8'
        code_base = re.sub(r"(?<=\.).+", "", code_with_dash)
    else:
        # if no '.' e.g. DHP1-20 return early
        return []

    # find the part with dashes, '5-8.' in 'SN12.5-8'
    code_dash = re.sub(code_base, "", code_with_dash)

    # find the first digit, 5 in 'SN12.5-8'
    code_first = int(re.sub(r"-.+", "", code_dash))

    # find the last digit, 8 in 'SN12.5-8'
    code_last = int(re.sub(r".+-", "", code_dash))

    sutta_code_list = []
    for num in range(code_first, code_last + 1):
        sutta_code_list.append(f"{code_base}{num}")
    return sutta_code_list


def make_list_of_sutta_codes(su: SuttaInfo) -> list[str]:
    sutta_codes_set: set[str] = set()
    sutta_codes_set.add(su.dpd_code)
    if "-" in su.dpd_code:
        sutta_codes_set.update(generate_range_of_sutta_codes(su.dpd_code))
    sutta_codes_set.add(su.sc_code)
    if "-" in su.sc_code:
        sutta_codes_set.update(generate_range_of_sutta_codes(su.sc_code))

    return pali_list_sorter(sutta_codes_set)


if __name__ == "__main__":
    su = SuttaInfo()
    su.dpd_code = "SN12.34-47"
    su.sc_code = "SN12.33-46"
    results = make_list_of_sutta_codes(su)
    print(results)
