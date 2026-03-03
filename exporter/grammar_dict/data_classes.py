from db.models import Lookup
from tools.paths import ProjectPaths
from tools.css_manager import CSSManager


class GrammarData:
    def __init__(self, lookup_entry: Lookup, pth: ProjectPaths, jinja_env):
        self.headword = lookup_entry.lookup_key
        self.grammar_data_list = lookup_entry.grammar_unpack
        self.rows = self._process_grammar(self.grammar_data_list)
        self.header = self._generate_header(pth, jinja_env)

    def _generate_header(self, pth: ProjectPaths, jinja_env) -> str:
        header_templ = jinja_env.get_template("grammar_dict_header.jinja")
        css_manager = CSSManager()
        # The original code called render(css="", js="")
        html_header = header_templ.render(css="", js="")
        html_header = css_manager.update_style(html_header, "primary")
        return html_header

    def _process_grammar(self, grammar_data_list):
        processed_rows = []
        for headword, pos, grammar_str in grammar_data_list:
            components = []
            if grammar_str.startswith("reflx"):
                parts = grammar_str.split()
                if len(parts) >= 2:
                    components.append(parts[0] + " " + parts[1])
                    components += parts[2:]
                else:
                    components.append(grammar_str)
            elif grammar_str.startswith("in comps"):
                components.append(grammar_str)
            else:
                components = grammar_str.split()

            while len(components) < 3:
                components.append("")

            processed_rows.append(
                {"pos": pos, "components": components, "headword": headword}
            )
        return processed_rows
