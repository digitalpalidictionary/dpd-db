"""Related scripts and styles must leave the browser cache together."""

import ast
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.templating import Jinja2Templates

from exporter.webapp.precompressed_index import digest

ASSETS = (
    "dpd.css",
    "home.css",
    "switch.css",
    "tt.css",
    "app.js",
    "home.js",
    "bold_definitions.js",
    "tipitaka_translations.js",
    "dpd.js",
    "sorter.js",
)


def asset_urls(static_dir: Path) -> dict[str, str]:
    templates = Jinja2Templates(directory="exporter/webapp/templates")
    source = Path("exporter/webapp/main.py")
    registration = next(
        node
        for node in ast.parse(source.read_text(encoding="utf-8")).body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and ast.unparse(node.value.func) == "templates.env.globals.update"
    )
    # Exercise the actual startup registration without loading the databases.
    exec(
        compile(ast.Module(body=[registration], type_ignores=[]), str(source), "exec"),
        {
            "templates": templates,
            "pth": SimpleNamespace(webapp_static_dir=static_dir),
            "digest": digest,
            "config_test": lambda *args: False,
        },
    )
    html = templates.get_template("home.html").render(
        request=SimpleNamespace(query_params={}),
        dpd_results="",
        book_options=[],
        bd_count=0,
        dpd_release_version="unchanged-database-release",
    )
    versions = dict(re.findall(r"static/([\w.]+\.(?:js|css))\?v=([0-9a-f]+)", html))
    # A script or style added later without a version would be missed above.
    loaded = set(re.findall(r"static/([\w./-]+\.(?:js|css))\b", html))
    assert loaded == set(versions), loaded - set(versions)
    return versions


@pytest.mark.parametrize("changed", ASSETS)
def test_any_asset_change_refreshes_all_related_urls(
    tmp_path: Path, changed: str
) -> None:
    for name in ASSETS:
        (tmp_path / name).write_text(name, encoding="utf-8")
    before = asset_urls(tmp_path)
    assert set(before) == set(ASSETS)
    assert len(set(before.values())) == 1
    assert asset_urls(tmp_path) == before

    (tmp_path / changed).write_text("updated content", encoding="utf-8")
    after = asset_urls(tmp_path)
    assert set(after) == set(ASSETS)
    assert len(set(after.values())) == 1
    assert all(after[name] != before[name] for name in ASSETS)
