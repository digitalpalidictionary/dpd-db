"""Commentary and late text source checking utilities.
This module provides functions to check if headwords have examples
only from late sources (commentaries, abhidhamma, grammar texts),
which should be treated as having no sutta examples.
"""

from db.models import DpdHeadword


# List of commentary and late text source codes
# If a word has examples only from these sources, it should be treated
# as having no sutta example and included in pass2pre processing
COMMENTARY_LIST: list[str] = [
    "VINa",
    "VINt",
    "DNa",
    "MNa",
    "SNa",
    "SNt",
    "ANa",
    "KHPa",
    "KPa",
    "DHPa",
    "UDa",
    "ITIa",
    "SNPa",
    "VVa",
    "VVt",
    "PVa",
    "THa",
    "THIa",
    "APAa",
    "APIa",
    "BVa",
    "CPa",
    "JAa",
    "NIDD1a",
    "NIDD2a",
    "PMa",
    "NPa",
    "NPt",
    "PTP",
    "DSa",
    "PPa",
    "VIBHa",
    "VIBHt",
    "ADHa",
    "ADHt",
    "KVa",
    "VMVt",
    "VSa",
    "PYt",
    "SDt",
    "SPV",
    "VAt",
    "VBt",
    "VISM",
    "VISMa",
    "PRS",
    "SDM",
    "SPM",
    "bālāvatāra",
    "kaccāyana",
    "saddanīti",
    "padarūpasiddhi",
    "buddhavandana",
]


def has_only_late_examples(i: DpdHeadword) -> bool:
    """
    Check if a headword has examples only from late sources
    """

    # Check if source_1 is a late source
    source_1_is_late = any(item in i.source_1 for item in COMMENTARY_LIST)

    if source_1_is_late and not i.source_2:
        return True

    source_2_is_late = any(item in i.source_2 for item in COMMENTARY_LIST)

    if source_1_is_late and source_2_is_late:
        return True

    return False


def is_missing_sutta_example(i: DpdHeadword) -> bool:
    """Check if a headword is missing a sutta example.
    Returns True if:
    - Has no example_1 at all
    - OR has only late (commentary) examples
    Returns False if:
    - Has at least one example from early sutta/vinaya sources
    """

    # Case 1: Has only late examples
    if has_only_late_examples(i):
        return True

    # Case 2: Has meaning_1 but no source_1
    if i.meaning_1 and not i.source_1:
        return True

    # Case 3: No meaning_1 at all
    if not i.meaning_1:
        return True

    return False
