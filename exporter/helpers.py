from dataclasses import dataclass
from pathlib import Path

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
    header_tmpl_path: Path
    dpd_definition_path: Path


def get_paths() -> ResourcePaths:

    pth = ResourcePaths(
        # directories
        templates_dir=Path("exporter/templates"),
        error_log_dir=Path("exporter/error_log"),
        # error log
        error_log_path=Path("exporter/error_log/error_log.tsv"),
        # css
        dpd_css_path=Path("exporter/css/dpd.css"),
        # javascript
        buttons_js_path=Path("exporter/javascript/buttons.js"),
        # templates
        header_tmpl_path=Path("exporter/templates/header.html"),
        dpd_definition_path=Path("exporter/templates/dpd_defintion.html"),


    )

    # ensure dirs exist
    for d in [
        pth.templates_dir,
        pth.error_log_dir,
    ]:
        d.mkdir(parents=True, exist_ok=True)

    return pth
