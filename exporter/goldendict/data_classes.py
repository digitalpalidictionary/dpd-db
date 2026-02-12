from typing import List, Set, Dict
from db.models import DpdHeadword, DpdRoot, FamilyCompound, FamilyIdiom, FamilyRoot, FamilySet, FamilyWord, SuttaInfo, Lookup
from tools.paths import ProjectPaths
from tools.meaning_construction import make_grammar_line
from tools.superscripter import superscripter_uni
from tools.pos import CONJUGATIONS, DECLENSIONS, INDECLINABLES
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
        fc: List[FamilyCompound],
        fi: List[FamilyIdiom],
        fs: List[FamilySet],
        su: SuttaInfo,
        pth: ProjectPaths,
        jinja_env,
        cf_set: Set[str],
        idioms_set: Set[str],
        show_id: bool
    ):
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
        self.header = self._generate_header()
        self.buttons = self._calculate_buttons()
        
    @staticmethod
    def _convert_newlines(obj):
        attrs = [
            "meaning_1", "sanskrit", "phonetic", "compound_construction",
            "commentary", "sutta_1", "sutta_2", "example_1", "example_2", "notes"
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
        html_header = template.render(data=self)
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "dpd")

    def _calculate_buttons(self) -> dict:
        button_html = '<a class="dpd-button" href="#" data-target="{target}">{name}</a>'
        res = {}
        res["play_button"] = ""
        if self.i.needs_audio_button:
            res["play_button"] = (
                f'<a class="dpd-button play" onclick="playAudio(\'{self.i.lemma_clean}\', this)" title="Play Audio">'
                '<svg viewBox="0 0 24 24" width="16px" height="16px" fill="currentColor" stroke="currentColor" stroke-width="0">'
                '<path d="M8 5v14l11-7z"></path>'
                "</svg>"
                "</a>"
            )
        res["sutta_info_button"] = button_html.format(target=f"sutta_info_{self.i.lemma_1_}", name="sutta") if self.i.needs_sutta_info_button else ""
        res["grammar_button"] = button_html.format(target=f"grammar_{self.i.lemma_1_}", name="grammar") if self.i.needs_grammar_button else ""
        res["example_button"] = button_html.format(target=f"example_{self.i.lemma_1_}", name="example") if self.i.needs_example_button else ""
        res["examples_button"] = button_html.format(target=f"examples_{self.i.lemma_1_}", name="examples") if self.i.needs_examples_button else ""
        res["conjugation_button"] = button_html.format(target=f"conjugation_{self.i.lemma_1_}", name="conjugation") if self.i.needs_conjugation_button else ""
        res["declension_button"] = button_html.format(target=f"declension_{self.i.lemma_1_}", name="declension") if self.i.needs_declension_button else ""
        res["root_family_button"] = button_html.format(target=f"family_root_{self.i.lemma_1_}", name="root family") if self.i.needs_root_family_button else ""
        res["word_family_button"] = button_html.format(target=f"family_word_{self.i.lemma_1_}", name="word family") if self.i.needs_word_family_button else ""
        if self.i.needs_compound_family_button:
            res["compound_family_button"] = button_html.format(target=f"family_compound_{self.i.lemma_1_}", name="compound family")
        elif self.i.needs_compound_families_button:
            res["compound_family_button"] = button_html.format(target=f"family_compound_{self.i.lemma_1_}", name="compound families")
        else:
            res["compound_family_button"] = ""
        res["idioms_button"] = button_html.format(target=f"family_idiom_{self.i.lemma_1_}", name="idioms") if self.i.needs_idioms_button else ""
        if self.i.needs_set_button:
            res["set_family_button"] = button_html.format(target=f"family_set_{self.i.lemma_1_}", name="set")
        elif self.i.needs_sets_button:
            res["set_family_button"] = button_html.format(target=f"family_set_{self.i.lemma_1_}", name="sets")
        else:
            res["set_family_button"] = ""
        res["frequency_button"] = button_html.format(target=f"frequency_{self.i.lemma_1_}", name="frequency") if self.i.needs_frequency_button else ""
        res["feedback_button"] = button_html.format(target=f"feedback_{self.i.lemma_1_}", name="feedback")
        return res


class RootsData:
    def __init__(self, r: DpdRoot, roots_count_dict: Dict[str, int], pth: ProjectPaths, jinja_env, frs: List[FamilyRoot]):
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
        html_header = template.render(data=self)
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
