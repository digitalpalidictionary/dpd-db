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
from tools.paths import ProjectPaths
from tools.printer import p_counter, p_green, p_green_title, p_title, p_yes
from tools.tic_toc import tic, toc
from tools.pali_sort_key import pali_list_sorter


class ProgData():
    def __init__(self) -> None:
        p_green("making prog data")
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.apicaevaiti_dict = defaultdict(list[str])
        self.lookup_db: list[Lookup] = self.db_session.query(Lookup).all()
        self.lookup_db_len: int = len(self.lookup_db)
        self.headwords_db: list[DpdHeadword] = self.db_session.query(DpdHeadword).all()
        self.headwords_db_len: int = len(self.headwords_db)
        p_yes("ok")


def make_apicaeveiti_dict(g: ProgData):
    """
    Make a dictionary of 
    {"clean inflection": ["sandhi"]}
    {"kataṃ": ["katañca", "katampi"]}
    
    """
    p_green_title("making apicaeveiti_dict")

    for counter, i in enumerate(g.lookup_db):
        if i.deconstructor:
            deconstructions = i.deconstructor_unpack
            for deconstruction in deconstructions:
                plus_count = deconstruction.count(" + ")
                if plus_count == 1:
                    deconstruction = re.sub(r" \[.+", "", deconstruction) # remove the rule
                    find_me = re.compile(r" \+ (api|ca|eva|iti|iva)$")
                    if re.findall(find_me, deconstruction):
                        clean_inflection = re.sub(find_me, "", deconstruction)
                        g.apicaevaiti_dict[clean_inflection].append(i.lookup_key)
        
        if counter % 100000 == 0:
            p_counter(counter, g.lookup_db_len, i.lookup_key)
    
    p_green("apicaeveiti_dict size")
    p_yes(len(g.apicaevaiti_dict))


def add_apicaevaiti_to_inflections(g: ProgData):
    """Update i.inflections with sandhi forms."""

    p_green_title("adding apicaevaiti to inflections")

    updated_list: list[str] = [] # which headwords get updated?
    for counter, i in enumerate(g.headwords_db):

        inflection_list = i.inflections_list
        api_ca_eva_iti_list = i.inflections_list_api_ca_eva_iti

        for inflection in inflection_list:
            if (
                g.apicaevaiti_dict[inflection] != []
                and g.apicaevaiti_dict[inflection] not in api_ca_eva_iti_list
            ):
                api_ca_eva_iti_list.extend(g.apicaevaiti_dict[inflection])

        api_ca_eva_iti_list = pali_list_sorter(set(api_ca_eva_iti_list))
        i.inflections_api_ca_eva_iti = ",".join(api_ca_eva_iti_list)
        updated_list.append(i.lemma_1)
            
        if counter % 10000 == 0:
            p_counter(counter, g.headwords_db_len, i.lemma_1)

    p_green("updating db")
    g.db_session.commit()
    p_yes(len(updated_list))


def main():
    tic()
    p_title("adding api ca eva iti to inflections and lookup table")
    g = ProgData()
    make_apicaeveiti_dict(g)    
    add_apicaevaiti_to_inflections(g)
    toc()


if __name__ == "__main__":
    main()
