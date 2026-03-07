from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.meaning_construction import make_grammar_line


class KindleData:
    def __init__(
        self,
        i: DpdHeadword,
        pth: ProjectPaths,
        jinja_env,
        counter: int,
        inflections: list[str],
        devanagari_inflections: list[str],
    ):
        self.i = i
        self.pth = pth
        self.jinja_env = jinja_env
        self.counter = counter
        self.inflections = inflections
        self.devanagari_inflections = devanagari_inflections

        # Ported logic from render_ebook_entry
        self.summary = self._generate_summary()
        self._make_html_friendly()

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

    def _make_html_friendly(self):
        attrs = [
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
        ]
        for attr in attrs:
            val = getattr(self.i, attr)
            if isinstance(val, str):
                setattr(self.i, attr, self._html_friendly(val))

    def _html_friendly(self, text: str) -> str:
        try:
            text = text.replace("\n", "<br/>")
            text = text.replace(" > ", " &gt; ")
            text = text.replace(" < ", " &lt; ")
            return text
        except Exception:
            return text

    def _render_grammar_table(self) -> str:
        if self.i.meaning_1:
            grammar = make_grammar_line(self.i)
            template = self.jinja_env.get_template("ebook_grammar.jinja")
            html = template.render(
                i=self.i, grammar=grammar, meaning=self.i.meaning_combo_html
            )
            if "&" in html:
                html = html.replace(" & ", " &amp; ")
            return html
        return ""

    def _render_examples(self) -> str:
        if self.i.meaning_1 and self.i.example_1:
            template = self.jinja_env.get_template("ebook_example.jinja")
            return template.render(i=self.i)
        return ""
