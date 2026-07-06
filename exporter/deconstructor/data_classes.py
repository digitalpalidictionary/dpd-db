from jinja2 import Environment

from db.models import Lookup
from tools.css_manager import CSSManager
from tools.utils import squash_whitespaces
from exporter.goldendict.helpers import TODAY


class DeconstructorData:
    def __init__(self, result: Lookup) -> None:
        self.headword = result.lookup_key
        self.deconstructions = result.deconstructor_unpack
        self.today = TODAY


def generate_deconstructor_header(jinja_env: Environment) -> str:
    """Render the constant deconstructor header once.

    The header has no per-entry variables, so it is identical for every entry
    and is rendered a single time per run instead of once per compound.
    """
    header_templ = jinja_env.get_template("deconstructor_header.jinja")
    css_manager = CSSManager()
    html_header = header_templ.render(css="", js="")
    html_header = css_manager.update_style(html_header, "deconstructor")
    return squash_whitespaces(html_header)
