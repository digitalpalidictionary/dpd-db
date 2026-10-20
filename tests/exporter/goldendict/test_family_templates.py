"""Family headings in the GoldenDict JS templates agree in number with each family's count."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

JS_DIR = Path("exporter/goldendict/javascript")

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs node")


def _run_js(template: str, js_globals: dict[str, object], call: str) -> str:
    """Load the real template file in node and return what `call` renders."""
    script = f"""
const fs = require("fs");
globalThis.superScripter = (t) => t;
Object.assign(globalThis, {json.dumps(js_globals)});
(0, eval)(fs.readFileSync({json.dumps(str(JS_DIR / template))}, "utf8"));
process.stdout.write({call});
"""
    result = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=True
    )
    return result.stdout


def _family(count: int) -> dict[str, object]:
    return {"count": count, "data": [["word", "masc", "meaning", "✔"]]}


def _data(**kwargs: object) -> dict[str, object]:
    return {"lemma": "test word", "id": 1, "date": "2026-10-20", **kwargs}


def _compound_html(counts: dict[str, int]) -> str:
    return _run_js(
        "family_compound_template.js",
        {
            "family_compound_json": {k: _family(v) for k, v in counts.items()},
            "data": _data(family_compounds=list(counts)),
        },
        "makeFamilyCompoundHtml(data)",
    )


def _idiom_html(counts: dict[str, int]) -> str:
    return _run_js(
        "family_idiom_template.js",
        {
            "family_idiom_json": {k: _family(v) for k, v in counts.items()},
            "data": _data(family_idioms=list(counts)),
        },
        "makeFamilyIdioms(data)",
    )


def _root_html(count: int) -> str:
    fr = {
        "root_family": "√kar",
        "root_meaning": "do",
        **_family(count),
    }
    return _run_js(
        "family_root_template.js",
        {"fr": fr, "data": _data()},
        'makeFamilyRootHtml(data, fr, "lemma")',
    )


def _heading_is_closed(html: str) -> bool:
    heading = html[html.index('<p class="heading underlined"') : html.index("<table")]
    return "</p>" in heading


def test_compound_single_family_many_members_is_plural() -> None:
    assert "<b>16</b> compounds which contain " in _compound_html({"nibbidā": 16})


def test_compound_single_family_one_member_is_singular() -> None:
    assert "<b>1</b> compound which contains " in _compound_html({"nibbidā": 1})


def test_compound_several_families_follow_each_count() -> None:
    html = _compound_html({"kata": 1, "kara": 3})
    assert html.count("<b>1</b> compound which contains ") == 1
    assert html.count("<b>3</b> compounds which contain ") == 1


def test_compound_single_family_heading_is_closed() -> None:
    assert _heading_is_closed(_compound_html({"nibbidā": 16}))


def test_idiom_single_family_many_members_is_plural() -> None:
    assert "<b>4</b> idiomatic expressions which contain " in _idiom_html({"kāya": 4})


def test_idiom_single_family_one_member_is_singular() -> None:
    assert "<b>1</b> idiomatic expression which contains " in _idiom_html({"kāya": 1})


def test_idiom_several_families_follow_each_count() -> None:
    html = _idiom_html({"kāya": 1, "citta": 3})
    assert html.count("<b>1</b> idiomatic expression which contains ") == 1
    assert html.count("<b>3</b> idiomatic expressions which contain ") == 1


def test_idiom_single_family_heading_is_closed() -> None:
    assert _heading_is_closed(_idiom_html({"kāya": 4}))


def test_root_family_one_member_is_singular() -> None:
    assert "<b>1</b> word belongs to the root family " in _root_html(1)


def test_root_family_many_members_is_plural() -> None:
    assert "<b>5</b> words belong to the root family " in _root_html(5)


def test_set_single_family_heading_is_closed() -> None:
    html = _run_js(
        "family_set_template.js",
        {
            "family_set_json": {"colours": _family(4)},
            "data": _data(family_sets=["colours"]),
        },
        "makeFamilySets(data)",
    )
    assert _heading_is_closed(html)
