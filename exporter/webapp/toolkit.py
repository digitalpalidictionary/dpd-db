import difflib
import re
import time

from sqlalchemy.exc import OperationalError

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot, FamilyRoot, Lookup
from exporter.webapp.data_classes import (
    AbbreviationsData,
    DeconstructorData,
    EpdData,
    GrammarData,
    HeadwordData,
    HelpData,
    ManualVariantData,
    RootsData,
    SpellingData,
    VariantData,
)
from tools.exporter_functions import (
    get_family_compounds,
    get_family_idioms,
    get_family_set,
)
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.variants_manager import VariantManager


_variant_manager: VariantManager | None = None


def get_variant_manager() -> VariantManager:
    global _variant_manager
    if _variant_manager is None:
        _variant_manager = VariantManager()
    return _variant_manager


def make_dpd_html(
    q: str,
    pth: ProjectPaths,
    templates,
    roots_count_dict,
    headwords_clean_set,
    ascii_to_unicode_dict,
) -> tuple[str, str]:
    retries = 3
    vm = get_variant_manager()

    for attempt in range(retries):
        try:
            with get_db_session(pth.dpd_db_path) as db_session:
                with db_session.no_autoflush:
                    dpd_html = ""
                    summary_html = ""
                    q = q.replace("'", "").replace("ṁ", "ṃ").strip()

                    lookup_results = (
                        db_session.query(Lookup)
                        .filter(Lookup.lookup_key.ilike(q))
                        .all()
                    )

                    # Check manual variants from TSV first
                    main_form = vm.get_main(q)
                    if main_form:
                        d = ManualVariantData(variant=q, main=main_form)
                        summary_html += templates.get_template(
                            pth.template_manual_variant_summary
                        ).render(d=d)
                        dpd_html += templates.get_template(
                            pth.template_manual_variant
                        ).render(d=d)

                    # first try the lookup table, if no results, then try other options
                    if lookup_results:
                        for lookup_result in lookup_results:
                            # headwords
                            if lookup_result.headwords:
                                headwords = lookup_result.headwords_unpack
                                headword_results = (
                                    db_session.query(DpdHeadword)
                                    .filter(DpdHeadword.id.in_(headwords))
                                    .all()
                                )
                                headword_results = sorted(
                                    headword_results,
                                    key=lambda x: pali_sort_key(x.lemma_1),
                                )
                                for i in headword_results:
                                    fc = get_family_compounds(i)
                                    fi = get_family_idioms(i)
                                    fs = get_family_set(i)
                                    d = HeadwordData(i, fc, fi, fs)
                                    summary_html += templates.get_template(
                                        pth.template_dpd_summary
                                    ).render(d=d)
                                    dpd_html += templates.get_template(
                                        pth.template_dpd_headword
                                    ).render(d=d)

                            # roots
                            if lookup_result.roots:
                                roots_list = lookup_result.roots_unpack
                                root_results = (
                                    db_session.query(DpdRoot)
                                    .filter(DpdRoot.root.in_(roots_list))
                                    .all()
                                )
                                for r in root_results:
                                    frs = db_session.query(FamilyRoot).filter(
                                        FamilyRoot.root_key == r.root
                                    )
                                    frs = sorted(
                                        frs, key=lambda x: pali_sort_key(x.root_family)
                                    )
                                    d = RootsData(r, frs, roots_count_dict)
                                    summary_html += templates.get_template(
                                        pth.template_root_summary
                                    ).render(d=d)
                                    dpd_html += templates.get_template(
                                        pth.template_root
                                    ).render(d=d)

                            # abbreviations
                            if lookup_result.abbrev:
                                d = AbbreviationsData(lookup_result)
                                summary_html += templates.get_template(
                                    pth.template_abbreviations_summary
                                ).render(d=d)
                                dpd_html += templates.get_template(
                                    pth.template_abbreviations
                                ).render(d=d)

                            # deconstructor
                            if lookup_result.deconstructor:
                                d = DeconstructorData(lookup_result)
                                summary_html += templates.get_template(
                                    pth.template_deconstructor_summary
                                ).render(d=d)
                                dpd_html += templates.get_template(
                                    pth.template_deconstructor
                                ).render(d=d)

                            # grammar
                            if lookup_result.grammar:
                                d = GrammarData(lookup_result)
                                summary_html += templates.get_template(
                                    pth.template_grammar_summary
                                ).render(d=d)
                                dpd_html += templates.get_template(
                                    pth.template_grammar
                                ).render(d=d)

                            # help
                            if lookup_result.help:
                                d = HelpData(lookup_result)
                                summary_html += templates.get_template(
                                    pth.template_help_summary
                                ).render(d=d)
                                dpd_html += templates.get_template(
                                    pth.template_help
                                ).render(d=d)

                            # epd
                            if lookup_result.epd:
                                d = EpdData(lookup_result)
                                summary_html += templates.get_template(
                                    pth.template_epd_summary
                                ).render(d=d)
                                dpd_html += templates.get_template(
                                    pth.template_epd
                                ).render(d=d)

                            # variant
                            if lookup_result.variant:
                                d = VariantData(lookup_result)
                                summary_html += templates.get_template(
                                    pth.template_variant_summary
                                ).render(d=d)
                                dpd_html += templates.get_template(
                                    pth.template_variant
                                ).render(d=d)

                            # spelling mistake
                            if lookup_result.spelling:
                                d = SpellingData(lookup_result)
                                summary_html += templates.get_template(
                                    pth.template_spelling_summary
                                ).render(d=d)
                                dpd_html += templates.get_template(
                                    pth.template_spelling
                                ).render(d=d)

                    # the two cases below search directly in the DpdHeadwords table
                    elif q.isnumeric():  # eg 78654
                        search_term = int(q)
                        headword_result = (
                            db_session.query(DpdHeadword)
                            .filter(DpdHeadword.id == search_term)
                            .first()
                        )
                        if headword_result:
                            fc = get_family_compounds(headword_result)
                            fi = get_family_idioms(headword_result)
                            fs = get_family_set(headword_result)
                            d = HeadwordData(headword_result, fc, fi, fs)
                            dpd_html += templates.get_template(
                                pth.template_dpd_headword
                            ).render(d=d)

                        # return closest matches
                        else:
                            dpd_html = find_closest_matches(
                                q, headwords_clean_set, ascii_to_unicode_dict
                            )

                    elif re.search(r"\s\d", q):  # eg "kata 5"
                        headword_result = (
                            db_session.query(DpdHeadword)
                            .filter(DpdHeadword.lemma_1 == q)
                            .first()
                        )
                        if headword_result:
                            fc = get_family_compounds(headword_result)
                            fi = get_family_idioms(headword_result)
                            fs = get_family_set(headword_result)
                            d = HeadwordData(headword_result, fc, fi, fs)
                            dpd_html += templates.get_template(
                                pth.template_dpd_headword
                            ).render(d=d)

                        # return closest matches
                        else:
                            dpd_html = find_closest_matches(
                                q, headwords_clean_set, ascii_to_unicode_dict
                            )

                    # or finally return closest matches
                    else:
                        dpd_html = find_closest_matches(
                            q, headwords_clean_set, ascii_to_unicode_dict
                        )

                    return dpd_html, summary_html

        except OperationalError as e:
            if attempt == retries - 1:  # Last attempt
                raise e
            time.sleep(0.1 * (attempt + 1))  # Exponential backoff
        dpd_html = ""
        summary_html = ""
        q = q.replace("'", "").replace("ṁ", "ṃ").strip()

        lookup_results = (
            db_session.query(Lookup).filter(Lookup.lookup_key.ilike(q)).all()
        )

        # Check manual variants from TSV first
        main_form = vm.get_main(q)
        if main_form:
            d = ManualVariantData(variant=q, main=main_form)
            summary_html += templates.get_template(
                pth.template_manual_variant_summary
            ).render(d=d)
            dpd_html += templates.get_template(pth.template_manual_variant).render(d=d)

        # first try the lookup table, if no results, then try other options

        if lookup_results:
            for lookup_result in lookup_results:
                # headwords
                if lookup_result.headwords:
                    headwords = lookup_result.headwords_unpack
                    headword_results = (
                        db_session.query(DpdHeadword)
                        .filter(DpdHeadword.id.in_(headwords))
                        .all()
                    )
                    headword_results = sorted(
                        headword_results, key=lambda x: pali_sort_key(x.lemma_1)
                    )
                    for i in headword_results:
                        fc = get_family_compounds(i)
                        fi = get_family_idioms(i)
                        fs = get_family_set(i)
                        d = HeadwordData(i, fc, fi, fs)
                        summary_html += templates.get_template(
                            pth.template_dpd_summary
                        ).render(d=d)
                        dpd_html += templates.get_template(
                            pth.template_dpd_headword
                        ).render(d=d)

                # roots
                if lookup_result.roots:
                    roots_list = lookup_result.roots_unpack
                    root_results = (
                        db_session.query(DpdRoot)
                        .filter(DpdRoot.root.in_(roots_list))
                        .all()
                    )
                    for r in root_results:
                        frs = db_session.query(FamilyRoot).filter(
                            FamilyRoot.root_key == r.root
                        )
                        frs = sorted(frs, key=lambda x: pali_sort_key(x.root_family))
                        d = RootsData(r, frs, roots_count_dict)
                        summary_html += templates.get_template(
                            pth.template_root_summary
                        ).render(d=d)
                        dpd_html += templates.get_template(pth.template_root).render(
                            d=d
                        )

                # abbreviations
                if lookup_result.abbrev:
                    d = AbbreviationsData(lookup_result)
                    summary_html += templates.get_template(
                        pth.template_abbreviations_summary
                    ).render(d=d)
                    dpd_html += templates.get_template(
                        pth.template_abbreviations
                    ).render(d=d)

                # deconstructor
                if lookup_result.deconstructor:
                    d = DeconstructorData(lookup_result)
                    summary_html += templates.get_template(
                        pth.template_deconstructor_summary
                    ).render(d=d)
                    dpd_html += templates.get_template(
                        pth.template_deconstructor
                    ).render(d=d)

                # variant
                if lookup_result.variant:
                    d = VariantData(lookup_result)
                    summary_html += templates.get_template(
                        pth.template_variant_summary
                    ).render(d=d)
                    dpd_html += templates.get_template(pth.template_variant).render(d=d)

                # spelling mistake
                if lookup_result.spelling:
                    d = SpellingData(lookup_result)
                    summary_html += templates.get_template(
                        pth.template_spelling_summary
                    ).render(d=d)
                    dpd_html += templates.get_template(pth.template_spelling).render(
                        d=d
                    )

                # grammar
                if lookup_result.grammar:
                    d = GrammarData(lookup_result)
                    summary_html += templates.get_template(
                        pth.template_grammar_summary
                    ).render(d=d)
                    dpd_html += templates.get_template(pth.template_grammar).render(d=d)

                # help
                if lookup_result.help:
                    d = HelpData(lookup_result)
                    summary_html += templates.get_template(
                        pth.template_help_summary
                    ).render(d=d)
                    dpd_html += templates.get_template(pth.template_help).render(d=d)

                # epd
                if lookup_result.epd:
                    d = EpdData(lookup_result)
                    summary_html += templates.get_template(
                        pth.template_epd_summary
                    ).render(d=d)
                    dpd_html += templates.get_template(pth.template_epd).render(d=d)

        # the two cases below search directly in the DpdHeadwords table

        elif q.isnumeric():  # eg 78654
            search_term = int(q)
            headword_result = (
                db_session.query(DpdHeadword)
                .filter(DpdHeadword.id == search_term)
                .first()
            )
            if headword_result:
                fc = get_family_compounds(headword_result)
                fi = get_family_idioms(headword_result)
                fs = get_family_set(headword_result)
                d = HeadwordData(headword_result, fc, fi, fs)
                dpd_html += templates.get_template(pth.template_dpd_headword).render(
                    d=d
                )

            # return closest matches
            else:
                dpd_html = find_closest_matches(
                    q, headwords_clean_set, ascii_to_unicode_dict
                )

        elif re.search(r"\s\d", q):  # eg "kata 5"
            headword_result = (
                db_session.query(DpdHeadword).filter(DpdHeadword.lemma_1 == q).first()
            )
            if headword_result:
                fc = get_family_compounds(headword_result)
                fi = get_family_idioms(headword_result)
                fs = get_family_set(headword_result)
                d = HeadwordData(headword_result, fc, fi, fs)
                dpd_html += templates.get_template(pth.template_dpd_headword).render(
                    d=d
                )

            # return closest matches
            else:
                dpd_html = find_closest_matches(
                    q, headwords_clean_set, ascii_to_unicode_dict
                )

        # or finally return closest matches

        else:
            dpd_html = find_closest_matches(
                q, headwords_clean_set, ascii_to_unicode_dict
            )

    return dpd_html, summary_html


def find_closest_matches(
    q,
    headwords_clean_set,
    ascii_to_unicode_dict,
) -> str:
    ascii_matches = ascii_to_unicode_dict[q]
    closest_headword_matches = difflib.get_close_matches(
        q, headwords_clean_set, n=10, cutoff=0.7
    )

    combined_list = []
    combined_list.extend(ascii_matches)
    combined_list.extend(
        [item for item in closest_headword_matches if item not in ascii_matches]
    )

    string = '<h3 class="dpd">No results found. '
    if combined_list:
        string += "The closest matches are:</h3><br>"
        string += "<p>"
        string += ", ".join(combined_list)
        string += "</p>"
    else:
        string += "</h3>"

    return string


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
