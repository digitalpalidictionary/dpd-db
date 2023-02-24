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


@dataclass()
class ResourcePaths():
    # directories
    templates_dir: Path
    error_log_dir: Path
    # error log
    error_log_path: Path
    # css
    dpd_css_path: Path
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


def get_paths() -> ResourcePaths:

    pth = ResourcePaths(
        # directories
        templates_dir=Path(
            "exporter/templates"),
        error_log_dir=Path(
            "exporter/error_log"),

        # error log
        error_log_path=Path(
            "exporter/error_log/error_log.tsv"),

        # css
        dpd_css_path=Path(
            "exporter/css/dpd.css"),

        # javascript
        buttons_js_path=Path(
            "exporter/javascript/buttons.js"),

        # templates
        header_templ_path=Path(
            "exporter/templates/header.html"),
        dpd_definition_templ_path=Path(
            "exporter/templates/dpd_defintion.html"),
        button_box_templ_path=Path(
            "exporter/templates/button_box.html"),
        grammar_templ_path=Path(
            "exporter/templates/grammar.html"),
        example_templ_path=Path(
            "exporter/templates/example.html"),
        inflection_templ_path=Path(
            "exporter/templates/inflection.html"),
        family_root_templ_path=Path(
            "exporter/templates/family_root.html"),
        )

    # ensure dirs exist
    for d in [
        pth.templates_dir,
        pth.error_log_dir,
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


EXCLUDE_FROM_CATEGORIES: set = {
    "dps", "ncped", "pass1", "sandhi"}

EXCLUDE_FROM_FREQ: set = {
    "abbrev", "cs", "idiom", "letter", "prefix", "root", "suffix", "ve"}
