from jinja2 import Environment

from db.models import DpdHeadword
from tools.meaning_construction import make_grammar_line

_FRIENDLY_ATTRS = (
    "root_base",
    "construction",
    "sanskrit",
    "compound_type",
    "phonetic",
    "example_1",
    "example_2",
    "sutta_1",
    "sutta_2",
    "commentary",
    "notes",
    "cognate",
)


def html_friendly(text: str) -> str:
    """Make DPD plain text safe to embed as XHTML: newlines become <br/>,
    and stray angle brackets used as literal text (not markup) are escaped."""
    text = text.replace("\n", "<br/>")
    text = text.replace(" > ", " &gt; ")
    text = text.replace(" < ", " &lt; ")
    return text


def _make_friendly(headword: DpdHeadword) -> dict[str, str]:
    """Precompute html-friendly text for the fields kindle templates render
    as raw HTML, without mutating the ORM-tracked headword."""
    return {
        attr: html_friendly(val)
        for attr in _FRIENDLY_ATTRS
        if isinstance((val := getattr(headword, attr)), str)
    }


class KindleData:
    def __init__(
        self,
        i: DpdHeadword,
        jinja_env: Environment,
        counter: int,
        inflections: list[str],
        script_inflections: list[str] | None = None,
    ) -> None:
        self.i = i
        self.jinja_env = jinja_env
        self.counter = counter
        self.inflections = inflections
        self.script_inflections = script_inflections or []
        self.friendly: dict[str, str] = _make_friendly(i) if i.meaning_1 else {}

        self.summary = self._generate_summary()
        self.grammar_table = self._render_grammar_table()
        self.examples = self._render_examples()

    def _generate_summary(self) -> str:
        summary = f"{self.i.pos}. "
        if self.i.plus_case:
            summary += f"({self.i.plus_case}) "
        summary += self.i.meaning_combo_html

        construction = self.i.construction_summary
        if construction:
            summary += f" [{construction}]"

        summary += f" {self.i.degree_of_completion_html}"

        if "&" in summary:
            summary = summary.replace(" & ", " &amp; ")
        return summary

    def _render_grammar_table(self) -> str:
        if self.i.meaning_1:
            grammar = make_grammar_line(self.i)
            template = self.jinja_env.get_template("ebook_grammar.jinja")
            html = template.render(
                i=self.i,
                friendly=self.friendly,
                grammar=grammar,
                meaning=self.i.meaning_combo_html,
            )
            if "&" in html:
                html = html.replace(" & ", " &amp; ")
            return html
        return ""

    def _render_examples(self) -> str:
        if self.i.meaning_1 and self.i.example_1:
            template = self.jinja_env.get_template("ebook_example.jinja")
            return template.render(i=self.i, friendly=self.friendly)
        return ""
