from typing import Set
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
        jinja_env,
        cf_set: Set[str],
        idioms_set: Set[str],
        show_id: bool,
    ):
        self.construction_summary = i.construction_summary
        self.i = self._convert_newlines(i)
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

    @staticmethod
    def _convert_newlines(obj):
        attrs = [
            "construction",
            "phonetic",
            "compound_construction",
            "sutta_1",
            "sutta_2",
            "example_1",
            "example_2",
            "commentary",
            "notes",
            "link",
        ]
        for attr_name in attrs:
            attr_value = getattr(obj, attr_name, None)
            if isinstance(attr_value, str) and attr_value:
                try:
                    setattr(obj, attr_name, attr_value.replace("\n", "<br>"))
                except AttributeError:
                    continue
        return obj

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("dpd_header.jinja")
        html_header = template.render(d=self)
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "dpd")


class RootsData:
    def __init__(
        self,
        r: DpdRoot,
        roots_count_dict: dict[str, int],
        pth: ProjectPaths,
        jinja_env,
        frs: list[FamilyRoot],
    ):
        self.r = self._convert_newlines(r)
        self.pth = pth
        self.jinja_env = jinja_env
        self.today = TODAY
        self.date = str(TODAY)
        try:
            self.count = roots_count_dict[r.root]
        except KeyError:
            self.count = 0
        self.frs = sorted(frs, key=lambda x: pali_sort_key(x.root_family))
        self.header = self._generate_header()

    @staticmethod
    def _convert_newlines(obj):
        attrs = ["panini_root", "panini_sanskrit", "panini_english"]
        for attr_name in attrs:
            attr_value = getattr(obj, attr_name, None)
            if isinstance(attr_value, str) and attr_value:
                try:
                    setattr(obj, attr_name, attr_value.replace("\n", "<br>"))
                except AttributeError:
                    continue
        return obj

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("root_header.jinja")
        html_header = template.render(d=self)
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "root")


class EpdData:
    def __init__(self, lookup_entry: Lookup, pth: ProjectPaths, jinja_env):
        self.lookup_key = lookup_entry.lookup_key
        self.epd_entries = lookup_entry.epd_unpack
        self.pth = pth
        self.jinja_env = jinja_env
        self.html_string = self._generate_html_string()
        self.header = self._generate_header()

    def _generate_html_string(self) -> str:
        html_entries = []
        for lemma_clean, pos, meaning_plus_case in self.epd_entries:
            entry_html = f"<b class='epd'>{lemma_clean}</b> {pos}. {meaning_plus_case}"
            html_entries.append(entry_html)
        return "<br>".join(html_entries)

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("dpd_header_plain.jinja")
        html_header = template.render()
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "primary")


class VariantData:
    def __init__(self, variant: str, main: str, jinja_env):
        self.variant = variant
        self.main = main
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("dpd_header_plain.jinja")
        html_header = template.render()
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "primary")


class SeeData:
    def __init__(self, see: str, headword: str, jinja_env):
        self.see = see
        self.headword = headword
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("dpd_header_plain.jinja")
        html_header = template.render()
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "primary")


class SpellingData:
    def __init__(self, mistake: str, correction: str, jinja_env):
        self.mistake = mistake
        self.correction = correction
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("dpd_header_plain.jinja")
        html_header = template.render()
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "primary")


class AbbreviationsData:
    def __init__(self, i, jinja_env):
        self.i = i
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("dpd_header_plain.jinja")
        html_header = template.render()
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "secondary")


class HelpData:
    def __init__(self, i, jinja_env):
        self.i = i
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("dpd_header_plain.jinja")
        html_header = template.render()
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "secondary")
