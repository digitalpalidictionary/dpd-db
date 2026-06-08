from jinja2 import Environment

from db.models import (
    DpdHeadword,
    DpdRoot,
    FamilyCompound,
    FamilyIdiom,
    FamilyRoot,
    FamilySet,
    FamilyWord,
    SuttaInfo,
    Lookup,
)
from tools.paths import ProjectPaths
from tools.meaning_construction import make_grammar_line
from tools.pos import CONJUGATIONS, DECLENSIONS
from exporter.goldendict.helpers import TODAY
from tools.date_and_time import year_month_day_dash
from tools.css_manager import CSSManager
from tools.pali_sort_key import pali_sort_key


def _render_header(
    jinja_env: Environment,
    template_name: str,
    style: str,
    context: dict[str, object] | None = None,
) -> str:
    template = jinja_env.get_template(template_name)
    html_header = template.render(**(context or {}))
    css_manager = CSSManager()
    return css_manager.update_style(html_header, style)


def _render_plain_header(jinja_env: Environment, style: str) -> str:
    return _render_header(jinja_env, "dpd_header_plain.jinja", style)


class _NewlineView:
    """Read-only view over a DpdHeadword that renders newlines as ``<br>`` on
    display fields, without mutating the tracked ORM object. Every other
    attribute is delegated unchanged."""

    _NL_ATTRS = frozenset(
        {
            "construction",
            "phonetic",
            "compound_construction",
            "sutta_1",
            "sutta_2",
            "example_1",
            "example_2",
            "commentary",
            "notes",
        }
    )

    def __init__(self, obj: DpdHeadword) -> None:
        object.__setattr__(self, "_obj", obj)

    def __getattr__(self, name: str):
        value = getattr(self._obj, name)
        if name in self._NL_ATTRS and isinstance(value, str) and value:
            return value.replace("\n", "<br>")
        return value


class HeadwordData:
    def __init__(
        self,
        i: DpdHeadword,
        rt: DpdRoot,
        fr: FamilyRoot,
        fw: FamilyWord,
        fc: list[FamilyCompound],
        fi: list[FamilyIdiom],
        fs: list[FamilySet],
        su: SuttaInfo,
        pth: ProjectPaths,
        jinja_env: Environment,
        cf_set: set[str],
        idioms_set: set[str],
        show_id: bool,
    ) -> None:
        self.construction_summary = i.construction_summary
        self.i = _NewlineView(i)
        self.rt = rt
        self.fr = fr
        self.fw = fw
        self.fc = fc
        self.fi = fi
        self.fs = fs
        self.su = su
        self.pth = pth
        self.jinja_env = jinja_env
        self.cf_set = cf_set
        self.idioms_set = idioms_set
        self.show_id = show_id
        self.today = TODAY
        self.date = year_month_day_dash()
        self.grammar = make_grammar_line(i)
        self.meaning_combo_html = i.meaning_combo_html
        self.declensions = DECLENSIONS
        self.conjugations = CONJUGATIONS
        self.app_name = "GoldenDict"
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        return _render_header(self.jinja_env, "dpd_header.jinja", "dpd", {"d": self})


class RootsData:
    def __init__(
        self,
        r: DpdRoot,
        roots_count_dict: dict[str, int],
        pth: ProjectPaths,
        jinja_env: Environment,
        frs: list[FamilyRoot],
    ) -> None:
        self.r = r
        self.pth = pth
        self.jinja_env = jinja_env
        self.today = TODAY
        self.date = year_month_day_dash()
        try:
            self.count = roots_count_dict[r.root]
        except KeyError:
            self.count = 0
        self.frs = sorted(frs, key=lambda x: pali_sort_key(x.root_family))
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        return _render_header(self.jinja_env, "root_header.jinja", "root", {"d": self})


class EpdData:
    def __init__(
        self, lookup_entry: Lookup, pth: ProjectPaths, jinja_env: Environment
    ) -> None:
        self.lookup_key = lookup_entry.lookup_key
        self.epd_entries = lookup_entry.epd_unpack
        self.pth = pth
        self.jinja_env = jinja_env
        self.html_string = self._generate_html_string()
        self.header = self._generate_header()

    def _generate_html_string(self) -> str:
        return "<br>".join(
            f"<b class='epd'>{lemma_clean}</b> {pos}. {meaning_plus_case}"
            for lemma_clean, pos, meaning_plus_case in self.epd_entries
        )

    def _generate_header(self) -> str:
        return _render_plain_header(self.jinja_env, "primary")


class VariantData:
    def __init__(self, variant: str, main: str, jinja_env: Environment) -> None:
        self.variant = variant
        self.main = main
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        return _render_plain_header(self.jinja_env, "primary")


class SeeData:
    def __init__(self, see: str, headword: str, jinja_env: Environment) -> None:
        self.see = see
        self.headword = headword
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        return _render_plain_header(self.jinja_env, "primary")


class SpellingData:
    def __init__(self, mistake: str, correction: str, jinja_env: Environment) -> None:
        self.mistake = mistake
        self.correction = correction
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        return _render_plain_header(self.jinja_env, "primary")


class AbbreviationsData:
    def __init__(self, i, jinja_env: Environment) -> None:
        self.i = i
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        return _render_plain_header(self.jinja_env, "secondary")


class AbbrevOtherData:
    def __init__(
        self, abbreviation: str, rows: list[dict[str, str]], jinja_env: Environment
    ) -> None:
        self.abbreviation = abbreviation
        self.rows = rows
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        return _render_plain_header(self.jinja_env, "secondary")


class HelpData:
    def __init__(self, i, jinja_env: Environment) -> None:
        self.i = i
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        return _render_plain_header(self.jinja_env, "secondary")
