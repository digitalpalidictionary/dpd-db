from db.models import PaliWord
from tools.pali_alphabet import pali_alphabet


def find_first_letter(i: PaliWord):
    """Find the first letter, including aspirated double letters ch jh etc."""
    if len(i.pali_1) > 1:
        if i.pali_1[:2] in pali_alphabet:
            return i.pali_1[:2]
        else:
            return i.pali_1[0]
    else:
        return i.pali_1[0]
