#!/usr/bin/env python3

"""
Find all api ca eva iti iva in deconstructor and add to inflections and lookup table.

'api' 'ca' 'eva' 'iti' and 'iva' are the most common words appearing in sandhi compounds,
so in those cases, just show the actual inflected word itself first, then the deconstruction.
"""

import re
from collections import defaultdict

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class ProgData:
    def __init__(self) -> None:
        pr.green("making prog data")
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.apicaevaitihi_dict = defaultdict(list[str])
        self.lookup_db: list[Lookup] = self.db_session.query(Lookup).all()
        self.lookup_db_len: int = len(self.lookup_db)
        self.headwords_db: list[DpdHeadword] = self.db_session.query(DpdHeadword).all()
        self.headwords_db_len: int = len(self.headwords_db)
        pr.yes("ok")


def make_apicaevaitihi_dict(g: ProgData):
    """
    Make a dictionary of
    {"clean inflection": ["sandhi"]}
    {"kataṃ": ["katañca", "katampi"]}

    """
    pr.green_title("making apicaeveiti_dict")

    for counter, i in enumerate(g.lookup_db):
        if i.deconstructor:
            deconstructions = i.deconstructor_unpack
            for deconstruction in deconstructions:
                plus_count = deconstruction.count(" + ")
                if plus_count == 1:
                    deconstruction = re.sub(
                        r" \[.+", "", deconstruction
                    )  # remove the rule
                    find_me = re.compile(r" \+ (api|ca|eva|iti|iva|hi)$")
                    if re.findall(find_me, deconstruction):
                        clean_inflection = re.sub(find_me, "", deconstruction)
                        g.apicaevaitihi_dict[clean_inflection].append(i.lookup_key)

        if counter % 100000 == 0:
            pr.counter(counter, g.lookup_db_len, i.lookup_key)

    pr.green("apicaevaitihi_dict size")
    pr.yes(len(g.apicaevaitihi_dict))


def add_apicaevaitihi_to_inflections(g: ProgData):
    """Update i.inflections with sandhi forms."""

    pr.green_title("adding apicaevaitihi to inflections")

    updated_list: list[str] = []  # which headwords get updated?
    for counter, i in enumerate(g.headwords_db):
        inflection_list = i.inflections_list
        api_ca_eva_iti_list = i.inflections_list_api_ca_eva_iti

        for inflection in inflection_list:
            if (
                g.apicaevaitihi_dict[inflection] != []
                and g.apicaevaitihi_dict[inflection] not in api_ca_eva_iti_list
            ):
                api_ca_eva_iti_list.extend(g.apicaevaitihi_dict[inflection])

        api_ca_eva_iti_list = pali_list_sorter(set(api_ca_eva_iti_list))
        i.inflections_api_ca_eva_iti = ",".join(api_ca_eva_iti_list)
        updated_list.append(i.lemma_1)

        if counter % 10000 == 0:
            pr.counter(counter, g.headwords_db_len, i.lemma_1)

    pr.green("updating db")
    g.db_session.commit()
    pr.yes(len(updated_list))


def main():
    pr.tic()
    pr.title("adding api ca eva iti hi to inflections and lookup table")
    g = ProgData()
    make_apicaevaitihi_dict(g)
    add_apicaevaitihi_to_inflections(g)
    pr.toc()


if __name__ == "__main__":
    main()
