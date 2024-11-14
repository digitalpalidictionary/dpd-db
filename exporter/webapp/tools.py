import re
import difflib
from unidecode import unidecode

from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from exporter.webapp.modules import AbbreviationsData
from exporter.webapp.modules import DeconstructorData
from exporter.webapp.modules import EpdData
from exporter.webapp.modules import RpdData
from exporter.webapp.modules import GrammarData
from exporter.webapp.modules import HeadwordData
from exporter.webapp.modules import HelpData
from exporter.webapp.modules import RootsData
from exporter.webapp.modules import SpellingData
from exporter.webapp.modules import VariantData

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from db.models import DpdRoot
from db.models import FamilyRoot
from db.models import Lookup

from tools.exporter_functions import get_family_compounds
from tools.exporter_functions import get_family_idioms
from tools.exporter_functions import get_family_set
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.paths import ProjectPaths


def make_headwords_clean_set(db_session: Session, lang="en") -> set[str]:
    """Make a set of Pāḷi headwords and English meanings."""
    
    # add headwords
    results = db_session.query(DpdHeadword).all()
    headwords_clean_set = set([i.lemma_clean for i in results])

    if lang == "en":
        # add all english meanings
        results = db_session \
            .query(Lookup) \
            .filter(Lookup.epd != "") \
            .all()
        headwords_clean_set.update([i.lookup_key for i in results])

    if lang == "ru":
        # add all english and russian meanings
        results = db_session \
            .query(Lookup) \
            .filter(Lookup.epd != "") \
            .filter(Lookup.rpd != "") \
            .all()
        headwords_clean_set.update([i.lookup_key for i in results])
    
    return headwords_clean_set


def make_ascii_to_unicode_dict(db_session: Session) -> dict[str, list[str]]:
    """ASCII Key: Unicode Value."""

    results = db_session.query(DpdHeadword).all()
    headwords_clean_set: set[str] = set()
    for i in results:
        headwords_clean_set.add(i.lemma_clean)
        headwords_clean_set.add(i.lemma_2)
    headwords_sorted_list = pali_list_sorter(headwords_clean_set)

    ascii_to_unicode_dict = defaultdict(list)
    for headword in headwords_sorted_list:
        headword_ascii = unidecode(headword)
        if (
            headword_ascii != headword
            and headword not in ascii_to_unicode_dict[headword_ascii]
        ):
            ascii_to_unicode_dict[headword_ascii].append(headword)

    return ascii_to_unicode_dict


def make_dpd_html(q: str, pth: ProjectPaths, templates, roots_count_dict, headwords_clean_set, ascii_to_unicode_dict, lang="en") -> tuple[str, str]:
    db_session = get_db_session(pth.dpd_db_path)
    dpd_html = ""
    summary_html = ""
    q = q.replace("'", "").replace("ṁ", "ṃ").strip()

    if lang == "ru":
        q = q.casefold()

    lookup_results = db_session.query(Lookup) \
        .filter(Lookup.lookup_key.ilike(q)) \
        .all()
    
    # first try the lookup table, if no results, then try other options
    
    if lookup_results:
        for lookup_result in lookup_results:
        
            # headwords
            if lookup_result.headwords:
                headwords = lookup_result.headwords_unpack
                headword_results = db_session\
                    .query(DpdHeadword)\
                    .filter(DpdHeadword.id.in_(headwords))\
                    .options(joinedload(DpdHeadword.ru))\
                    .all()
                headword_results = sorted(
                    headword_results, key=lambda x: pali_sort_key(x.lemma_1))
                for i in headword_results:
                    fc = get_family_compounds(i)
                    fi = get_family_idioms(i)
                    fs = get_family_set(i)
                    d = HeadwordData(i, fc, fi, fs)
                    summary_html += templates \
                        .get_template("dpd_summary.html") \
                        .render(d=d)
                    dpd_html += templates \
                        .get_template("dpd_headword.html") \
                        .render(d=d)
            
            # roots
            if lookup_result.roots:
                roots_list = lookup_result.roots_unpack
                root_results = db_session \
                    .query(DpdRoot) \
                    .filter(DpdRoot.root.in_(roots_list))\
                    .all()
                for r in root_results:
                    frs = db_session \
                        .query(FamilyRoot) \
                        .filter(FamilyRoot.root_key == r.root)
                    frs = sorted(frs, key=lambda x: pali_sort_key(x.root_family))
                    d = RootsData(r, frs, roots_count_dict)
                    summary_html += templates \
                        .get_template("root_summary.html") \
                        .render(d=d)
                    dpd_html += templates \
                        .get_template("root.html") \
                        .render(d=d)

            # deconstructor
            if lookup_result.deconstructor:
                d = DeconstructorData(lookup_result)
                dpd_html += templates \
                    .get_template("deconstructor.html") \
                    .render(d=d)

            # variant
            if lookup_result.variant:
                d = VariantData(lookup_result)
                dpd_html += templates \
                    .get_template("variant.html") \
                    .render(d=d)

            # spelling mistake
            if lookup_result.spelling:
                d = SpellingData(lookup_result)
                dpd_html += templates \
                    .get_template("spelling.html") \
                    .render(d=d)

            if lookup_result.grammar:
                d = GrammarData(lookup_result)
                dpd_html += templates \
                    .get_template("grammar.html") \
                    .render(d=d)

            # help          
            if lookup_result.help:
                d = HelpData(lookup_result)
                dpd_html += templates \
                    .get_template("help.html") \
                    .render(d=d)

            # abbreviations
            if lookup_result.abbrev:
                d = AbbreviationsData(lookup_result)
                dpd_html += templates \
                    .get_template("abbreviations.html") \
                    .render(d=d)

            # epd 
            if lookup_result.epd:
                d = EpdData(lookup_result)
                dpd_html += templates \
                    .get_template("epd.html") \
                    .render(d=d)

            # rpd 
            if lang == "ru" and lookup_result.rpd:
                d = RpdData(lookup_result)
                dpd_html += templates \
                    .get_template("rpd.html") \
                    .render(d=d)

    # the two cases below search directly in the DpdHeadwords table

    elif q.isnumeric(): # eg 78654
        search_term = int(q)
        headword_result = db_session\
            .query(DpdHeadword)\
            .filter(DpdHeadword.id == search_term)\
            .options(joinedload(DpdHeadword.ru))\
            .first()
        if headword_result:
            fc = get_family_compounds(headword_result)
            fi = get_family_idioms(headword_result)
            fs = get_family_set(headword_result)
            d = HeadwordData(headword_result, fc, fi, fs)
            dpd_html += templates \
                .get_template("dpd_headword.html") \
                .render(d=d)

        # return closest matches
        else:
            dpd_html = find_closest_matches(q, headwords_clean_set, ascii_to_unicode_dict, lang)

    elif re.search(r"\s\d", q): # eg "kata 5"
        headword_result = db_session \
            .query(DpdHeadword) \
            .filter(DpdHeadword.lemma_1 == q) \
            .options(joinedload(DpdHeadword.ru))\
            .first()
        if headword_result:
            fc = get_family_compounds(headword_result)
            fi = get_family_idioms(headword_result)
            fs = get_family_set(headword_result)
            d = HeadwordData(headword_result, fc, fi, fs)
            dpd_html += templates \
                .get_template("dpd_headword.html") \
                .render(d=d)

        # return closest matches
        else:
            dpd_html = find_closest_matches(q, headwords_clean_set, ascii_to_unicode_dict, lang)

    # or finally return closest matches
    
    else:
        dpd_html = find_closest_matches(q, headwords_clean_set, ascii_to_unicode_dict, lang)

    db_session.close()
    return dpd_html, summary_html

    

def find_closest_matches(q, headwords_clean_set, ascii_to_unicode_dict, lang="en") -> str:

    ascii_matches = ascii_to_unicode_dict[q]
    closest_headword_matches =  \
        difflib.get_close_matches(
            q, headwords_clean_set,
            n=10,
            cutoff=0.7)
    
    combined_list = []
    combined_list.extend(ascii_matches)
    combined_list.extend([
        item 
        for item in closest_headword_matches
        if item not in ascii_matches
    ])

    if lang == "en":
        string = "<h3>No results found. "
        if combined_list:
            string += "The closest matches are:</h3><br>"
            string += "<p>"
            string += ", ".join(combined_list)
            string += "</p>"
        else:
            string += "</h3>"

    if lang == "ru":
        string = "<h3>Ничего не найдено. "
        if combined_list:
            string += "Ближайшие совпадения:</h3><br>"
            string += "<p>"
            string += ", ".join(combined_list)
            string += "</p>"
        else:
            string += "</h3>"

    return string

