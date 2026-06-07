#!/usr/bin/env python3

"""
Find all api ca eva iti iva hi in deconstructor and add to inflections and lookup table.

'api' 'ca' 'eva' 'iti' 'iva' 'hi' are the most common words appearing in sandhi compounds,
so in those cases, just show the actual inflected word itself first, then the deconstruction.
"""

import re
from collections import defaultdict

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import printer as pr

_RULE_RE = re.compile(r" \[.+")
_PARTICLE_RE = re.compile(r" \+ (api|ca|eva|iti|iva|hi)$")


class GlobalVars:
    def __init__(self) -> None:
        pr.green_tmr("making prog data")
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.apicaevaitihi_dict: defaultdict[str, list[str]] = defaultdict(list)
        self.lookup_db: list[Lookup] = (
            self.db_session.query(Lookup).filter(Lookup.deconstructor != "").all()
        )
        self.lookup_db_len: int = len(self.lookup_db)
        self.headwords_db: list[DpdHeadword] = self.db_session.query(DpdHeadword).all()
        self.headwords_db_len: int = len(self.headwords_db)
        pr.yes("ok")


def make_apicaevaitihi_dict(g: GlobalVars) -> None:
    """
    Make a dictionary of
    {"clean inflection": ["sandhi"]}
    {"kataṃ": ["katañca", "katampi"]}

    """
    pr.green_title("making apicaeveiti_dict")

    for counter, i in enumerate(g.lookup_db):
        for deconstruction in i.deconstructor_unpack:
            if deconstruction.count(" + ") == 1:
                deconstruction = _RULE_RE.sub("", deconstruction)  # remove the rule
                match = _PARTICLE_RE.search(deconstruction)
                if match:
                    clean_inflection = deconstruction[: match.start()]
                    g.apicaevaitihi_dict[clean_inflection].append(i.lookup_key)

        if counter % 100000 == 0:
            pr.counter(counter, g.lookup_db_len, i.lookup_key)

    pr.green_tmr("apicaevaitihi_dict size")
    pr.yes(len(g.apicaevaitihi_dict))


def add_apicaevaitihi_to_inflections(g: GlobalVars) -> None:
    """Update i.inflections with sandhi forms."""

    pr.green_title("adding apicaevaitihi to inflections")

    updated_count = 0
    for counter, i in enumerate(g.headwords_db):
        sandhi_forms: list[str] = list(i.inflections_list_api_ca_eva_iti)

        for inflection in i.inflections_list:
            sandhi_forms.extend(g.apicaevaitihi_dict.get(inflection, []))

        new_value = ",".join(pali_list_sorter(set(sandhi_forms)))
        if new_value != i.inflections_api_ca_eva_iti:
            i.inflections_api_ca_eva_iti = new_value
            updated_count += 1

        if counter % 10000 == 0:
            pr.counter(counter, g.headwords_db_len, i.lemma_1)

    pr.green_tmr("updating db")
    g.db_session.commit()
    pr.yes(updated_count)


def main() -> None:
    pr.tic()
    pr.yellow_title("adding api ca eva iti hi to inflections and lookup table")
    g = GlobalVars()
    make_apicaevaitihi_dict(g)
    add_apicaevaitihi_to_inflections(g)
    pr.toc()


if __name__ == "__main__":
    main()
