from dataclasses import dataclass
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import PaliWord

INDECLINEABLES = [
    "abbrev", "abs", "ger", "ind", "inf", "prefix",
    "sandhi", "suffix", "idiom", "var"
]

CONJUGATIONS = [
    "aor", "cond", "fut", "imp", "imperf", "opt", "perf", "pr"
]

DECLENSIONS = [
    "adj", "card", "cs", "fem", "letter", "masc", "nt", "ordin",
    "pp", "pron", "prp", "ptp", "root", "ve"
]

EXCLUDE_FROM_SETS: set = {
    "dps", "ncped", "pass1", "sandhi"}

EXCLUDE_FROM_FREQ: set = {
    "abbrev", "cs", "idiom", "letter", "prefix", "root", "suffix", "ve"}


@dataclass()
class ResourcePaths():
    # directories
    templates_dir: Path
    zip_dir: Path
    # css
    dpd_css_path: Path
    roots_css_path: Path
    sandhi_css_path: Path
    epd_css_path: Path
    help_css_path: Path
    # javascript
    buttons_js_path: Path
    # templates
    header_templ_path: Path
    dpd_definition_templ_path: Path
    button_box_templ_path: Path
    grammar_templ_path: Path
    example_templ_path: Path
    inflection_templ_path: Path
    family_root_templ_path: Path
    family_word_templ_path: Path
    family_compound_templ_path: Path
    family_set_templ_path: Path
    frequency_templ_path: Path
    feedback_templ_path: Path
    # output
    zip_path: Path
    # root templates
    root_definition_templ_path: Path
    root_button_templ_path: Path
    root_info_templ_path: Path
    root_matrix_templ_path: Path
    root_families_templ_path: Path
    # other templates
    sandhi_templ_path: Path
    epd_templ_path: Path
    abbrev_templ_path: Path
    help_templ_path: Path
    # help
    abbrev_tsv_path: Path
    help_tsv_path: Path
    bibliography_path: Path
    thanks_path: Path


def get_paths() -> ResourcePaths:

    pth = ResourcePaths(
        # directories
        templates_dir=Path(
            "exporter/templates"),
        zip_dir=Path(
            "exporter/share"
        ),

        # css
        dpd_css_path=Path(
            "exporter/css/dpd.css"),
        roots_css_path=Path(
            "exporter/css/roots.css"),
        sandhi_css_path=Path(
            "exporter/css/sandhi.css"),
        epd_css_path=Path(
            "exporter/css/epd.css"),
        help_css_path=Path(
            "exporter/css/help.css"),

        # javascript
        buttons_js_path=Path(
            "exporter/javascript/buttons.js"),

        # templates
        header_templ_path=Path(
            "exporter/templates/header.html"),
        dpd_definition_templ_path=Path(
            "exporter/templates/dpd_defintion.html"),
        button_box_templ_path=Path(
            "exporter/templates/dpd_button_box.html"),
        grammar_templ_path=Path(
            "exporter/templates/dpd_grammar.html"),
        example_templ_path=Path(
            "exporter/templates/dpd_example.html"),
        inflection_templ_path=Path(
            "exporter/templates/dpd_inflection.html"),
        family_root_templ_path=Path(
            "exporter/templates/dpd_family_root.html"),
        family_word_templ_path=Path(
            "exporter/templates/dpd_family_word.html"),
        family_compound_templ_path=Path(
            "exporter/templates/dpd_family_compound.html"),
        family_set_templ_path=Path(
            "exporter/templates/dpd_family_set.html"),
        frequency_templ_path=Path(
            "exporter/templates/dpd_frequency.html"),
        feedback_templ_path=Path(
            "exporter/templates/dpd_feedback.html"),

        # output
        zip_path=Path(
            "exporter/share/dpdv2.zip"),

        # root tempaltes
        root_definition_templ_path=Path(
            "exporter/templates/root_definition.html"),
        root_button_templ_path=Path(
            "exporter/templates/root_buttons.html"),
        root_info_templ_path=Path(
            "exporter/templates/root_info.html"),
        root_matrix_templ_path=Path(
            "exporter/templates/root_matrix.html"),
        root_families_templ_path=Path(
            "exporter/templates/root_families.html"),

        # other templates
        epd_templ_path=Path(
            "exporter/templates/epd.html"),
        sandhi_templ_path=Path(
            "exporter/templates/sandhi.html"),
        abbrev_templ_path=Path(
            "exporter/templates/help_abbrev.html"),
        help_templ_path=Path(
            "exporter/templates/help_help.html"),

        # help
        abbrev_tsv_path=Path(
            "exporter/help/abbreviations.tsv"),
        help_tsv_path=Path(
            "exporter/help/help.tsv"),
        bibliography_path=Path(
            "../digitalpalidictionary-website-source/src/bibliography.md"),
        thanks_path=Path(
            "../digitalpalidictionary-website-source/src/thanks.md")
        )

    # ensure dirs exist
    for d in [
        pth.zip_dir,
    ]:
        d.mkdir(parents=True, exist_ok=True)

    return pth


_cached_cf_set = None


def cf_set_gen():
    """generate a list of all compounds families"""
    global _cached_cf_set

    if _cached_cf_set is not None:
        return _cached_cf_set

    db_session = get_db_session("dpd.db")
    cf_db = db_session.query(
        PaliWord
    ).filter(PaliWord.family_compound != ""
             ).all()

    cf_set = set()
    for i in cf_db:
        cfs = i.family_compound.split(" ")
        for cf in cfs:
            cf_set.add(cf)

    _cached_cf_set = cf_set
    return cf_set


CF_SET: set = cf_set_gen()


def add_nigahitas(synonyms: list) -> list:
    """add various types of nigahitas to synonyms"""
    for synonym in synonyms:
        if "ṃ" in synonym:
            synonyms += [synonym.replace("ṃ", "ṁ")]
            synonyms += [synonym.replace("ṃ", "ŋ")]
    return synonyms
