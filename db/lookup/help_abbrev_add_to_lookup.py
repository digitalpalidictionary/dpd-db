#!/usr/bin/env python3

"""Add help and abbreviations to the Lookup table."""

from rich import print

from db.db_helpers import get_db_session
from db.models import Lookup
from tools.lookup_is_another_value import is_another_value
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.tsv_read_write import read_tsv_as_dict, read_tsv_as_dict_with_different_key


class ProgData():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)


def add_help(g: ProgData):
    print("[green]adding help")

    # first remove old abbreviations from the table
    results = g.db_session.query(Lookup).filter(Lookup.help != "").all()
    for r in results:
        if is_another_value(r, "help"):
            r.help = ""
        else:
            g.db_session.delete(r)
    
    help_data = read_tsv_as_dict(g.pth.help_tsv_path)

    # then update with new values
    for key, values in help_data.items():

        if key != "Русский":

            # query the key in Lookup table
            results = g.db_session.query(Lookup).filter_by(lookup_key=key).first()

            # if it exists, then update help column
            if results:
                results.help_pack(values["meaning"])
            
            # if not, add it
            else:
                lkp = Lookup()
                lkp.lookup_key = key
                lkp.help_pack(values["meaning"])
                g.db_session.add(lkp)

    # add ru help
    ru_help_data = read_tsv_as_dict_with_different_key(g.pth.help_tsv_path, 2)

    # then update with new values
    for key, values in ru_help_data.items():

        # query the key in Lookup table
        results = g.db_session.query(Lookup).filter_by(lookup_key=key).first()

        # if it exists, then update help column
        if results:
            results.help_pack(values["ru_meaning"])
        
        # if not, add it
        else:
            lkp = Lookup()
            lkp.lookup_key = key
            lkp.help_pack(values["ru_meaning"])
            g.db_session.add(lkp)
    
    g.db_session.commit()
    


def add_abbreviations(g: ProgData):
    """Add abbreviations to lookup"""
    print("[green]adding abbreviations")
    
    # first remove old abbreviations from the table
    results = g.db_session.query(Lookup).filter(Lookup.abbrev != "").all()
    for r in results:
        if is_another_value(r, "abbrev"):
            r.abbrev = ""
        else:
            g.db_session.delete(r)

    abbrevs = read_tsv_as_dict(g.pth.abbreviations_tsv_path)

    # then update with new values    
    for key, values in abbrevs.items():
    
        # query the key in Lookup table
        results = g.db_session.query(Lookup).filter_by(lookup_key=key).first()

        # if it exists, then update abbrev column
        if results:
            results.abbrev_pack(values)
        
        # if not, add it
        else:
            lu = Lookup()
            lu.lookup_key = key
            lu.abbrev_pack(values)
            g.db_session.add(lu)

    # add ru abbrev
    ru_abbrevs = read_tsv_as_dict_with_different_key(g.pth.abbreviations_tsv_path, 5)

    # then update with new values    
    for key, values in ru_abbrevs.items():
    
        # query the key in Lookup table
        results = g.db_session.query(Lookup).filter_by(lookup_key=key).first()

        # if it exists, then update abbrev column
        if results:
            results.abbrev_pack(values)
        
        # if not, add it
        else:
            lu = Lookup()
            lu.lookup_key = key
            lu.abbrev_pack(values)
            g.db_session.add(lu)
    
    g.db_session.commit()


def main():
    tic()
    print("[bright_yellow]adding help and abbreviations to lookup")
    g = ProgData()
    add_help(g)
    add_abbreviations(g)
    toc()


if __name__ == "__main__":
    main()