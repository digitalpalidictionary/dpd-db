from db.models import Lookup
from tools.paths import ProjectPaths
from tools.css_manager import CSSManager
from tools.utils import squash_whitespaces
from exporter.goldendict.helpers import TODAY


class DeconstructorData:
    def __init__(self, result: Lookup, pth: ProjectPaths, jinja_env):
        self.headword = result.lookup_key
        self.deconstructions = result.deconstructor_unpack
        self.today = TODAY
        self.header = self._generate_header(pth, jinja_env)

    def _generate_header(self, pth: ProjectPaths, jinja_env) -> str:
        header_templ = jinja_env.get_template("deconstructor_header.jinja")
        css_manager = CSSManager()
        html_header = header_templ.render(css="", js="")
        html_header = css_manager.update_style(html_header, "deconstructor")
        return squash_whitespaces(html_header)
