# ruff: noqa: E402

import sys
import types
from types import SimpleNamespace
from typing import cast

from jinja2 import Environment, FileSystemLoader

sys.modules.setdefault(
    "aksharamukha",
    cast(
        types.ModuleType,
        types.SimpleNamespace(
            transliterate=types.SimpleNamespace(process=lambda *args, **kwargs: "")
        ),
    ),
)

from db.models import SuttaInfo


def _make_template_data(su: SuttaInfo) -> SimpleNamespace:
    headword = SimpleNamespace(
        lemma_1="test headword",
        lemma_1_="test_headword",
        pos="nt",
        plus_case="",
        needs_audio_button=False,
        needs_sutta_info_button=True,
        needs_grammar_button=False,
        needs_example_button=False,
        needs_examples_button=False,
        needs_conjugation_button=False,
        needs_declension_button=False,
        needs_root_family_button=False,
        needs_word_family_button=False,
        needs_compound_family_button=False,
        needs_compound_families_button=False,
        needs_idioms_button=False,
        needs_set_button=False,
        needs_sets_button=False,
        needs_frequency_button=False,
    )
    return SimpleNamespace(
        i=headword,
        su=su,
        meaning="",
        summary="",
        complete="",
    )


def _render_template(su: SuttaInfo, show_tbw: bool = False) -> str:
    env = Environment(
        loader=FileSystemLoader("exporter/webapp/templates"), autoescape=False
    )
    env.globals["show_tbw"] = show_tbw
    d = _make_template_data(su)
    return env.get_template("dpd_headword.html").render(d=d)


def test_dpd_headword_renders_samyutta_button_and_sc_card_link() -> None:
    su = SuttaInfo()
    su.dpd_sutta = "devatāsaṃyutta"
    su.dpd_code = "SN1"
    su.sc_code = "SN1.1"
    su.sc_book = "Saṁyutta Nikāya 1.1"

    html = _render_template(su)

    assert 'name="sutta-info-button"' in html
    assert "saṃyutta</a>" in html
    assert "SC Saṃyutta Card" in html
    assert "SC Vagga Card" not in html


def test_dpd_headword_renders_vagga_button_and_sc_vagga_links() -> None:
    su = SuttaInfo()
    su.dpd_sutta = "buddhavagga"
    su.dpd_code = "AN8.1-10"
    su.sc_code = "AN8.1"
    su.sc_book = "Aṅguttara Nikāya 8.1"
    su.sc_vagga = "1. Mettāvagga"

    html = _render_template(su)

    assert 'name="sutta-info-button"' in html
    assert "vagga</a>" in html
    assert "SC Vagga Card" in html
    assert "Pāḷi Text" in html
    assert 'href="https://suttacentral.net/an8-mettavagga"' in html
    assert 'href="https://suttacentral.net/AN8.1/pli/ms"' in html
    assert 'href="https://suttacentral.net/AN8.1/en/sujato"' in html


def test_dpd_headword_pts_has_own_heading_without_dv_data() -> None:
    su = SuttaInfo()
    su.dpd_sutta = "brahmajālasutta"
    su.dpd_code = "DN1"
    su.dv_pts = "D i 1,7"

    html = _render_template(su)

    assert "Pali Text Society" in html
    assert "D i 1,7" in html
    assert "Dhamma Vinaya Tools" not in html


def test_dpd_headword_pts_precedes_dv_catalogue_heading() -> None:
    su = SuttaInfo()
    su.dpd_sutta = "brahmajālasutta"
    su.dpd_code = "DN1"
    su.dv_pts = "D i 1,7"
    su.dv_main_theme = "ethics"

    html = _render_template(su)

    assert html.index("Pali Text Society") < html.index("Dhamma Vinaya Tools")
    assert "ethics" in html


def test_dpd_headword_vagga_row_hides_pts_and_its_heading() -> None:
    su = SuttaInfo()
    su.dpd_sutta = "sīlakkhandhavaggapāḷi"
    su.dpd_code = "DN1-13"
    su.dv_pts = "D i 1,7"

    html = _render_template(su)

    assert "Pali Text Society" not in html
    assert "D i 1,7" not in html


def test_dpd_headword_treats_vagga_samyuttapali_as_vagga() -> None:
    su = SuttaInfo()
    su.dpd_sutta = "sagāthāvaggasaṃyuttapāḷi"
    su.dpd_code = "SN1-11"
    su.sc_code = "SN1.1"
    su.sc_book = "Saṁyutta Nikāya 1.1"

    html = _render_template(su)

    assert 'name="sutta-info-button"' in html
    assert "vagga</a>" in html
    assert "SC Vagga Card" in html
    assert (
        'href="https://suttacentral.net/pitaka/sutta/linked/sn/sn-sagathavaggasamyutta"'
        in html
    )


def test_dpd_headword_hides_tbw_legacy_by_default() -> None:
    su = SuttaInfo()
    su.dpd_sutta = "devatāsaṃyutta"
    su.dpd_code = "SN1"
    su.book_code = "SN"
    su.sc_code = "SN1.1"

    html = _render_template(su)

    assert "TBW Legacy" not in html


def test_dpd_headword_shows_tbw_legacy_when_enabled() -> None:
    su = SuttaInfo()
    su.dpd_sutta = "devatāsaṃyutta"
    su.dpd_code = "SN1"
    su.book_code = "SN"
    su.sc_code = "SN1.1"

    html = _render_template(su, show_tbw=True)

    assert "TBW Legacy" in html
    assert "https://f.dhamma.gift/bw/sn/sn1.1.html" in html


# The Dhamma.gift row is not gated on show_tbw, so it needs its own default-path
# assertion rather than riding along on the TBW toggle test.
def test_dpd_headword_shows_dhamma_gift_short_link() -> None:
    su = SuttaInfo()
    su.dpd_sutta = "devatāsaṃyutta"
    su.dpd_code = "SN1"
    su.book_code = "SN"
    su.sc_code = "SN1.1"

    html = _render_template(su)

    assert "Dhamma.gift" in html
    assert "https://dhamma.gift/sn1.1" in html


def _render_compound_families(counts: dict[str, int]) -> str:
    """Render the compound family block(s) and collapse whitespace."""
    su = SuttaInfo()
    su.dpd_sutta = "devatāsaṃyutta"
    su.dpd_code = "SN1"
    d = _make_template_data(su)
    d.i.needs_sutta_info_button = False
    d.i.needs_compound_family_button = len(counts) == 1
    d.i.needs_compound_families_button = len(counts) > 1
    d.fc = [
        SimpleNamespace(count=count, compound_family=family, html="<table></table>")
        for family, count in counts.items()
    ]
    env = Environment(
        loader=FileSystemLoader("exporter/webapp/templates"), autoescape=False
    )
    html = env.get_template("dpd_headword.html").render(d=d)
    return " ".join(html.split())


def _family_heading(html: str, family: str) -> str:
    start = html.index(f'id="test_headwordcf_{family}"')
    return html[start : html.index("</p>", start)]


def test_dpd_headword_single_compound_family_many_members_is_plural() -> None:
    html = _render_compound_families({"nibbidā": 16})

    assert "<b> 16 </b> compounds which contain <b> nibbidā </b>" in html


def test_dpd_headword_single_compound_family_one_member_is_singular() -> None:
    html = _render_compound_families({"nibbidā": 1})

    assert "<b> 1 </b> compound which contains <b> nibbidā </b>" in html


def test_dpd_headword_several_compound_families_follow_each_count() -> None:
    html = _render_compound_families({"kata": 1, "kara": 3})

    assert "<b>1</b> compound which contains <b>kata</b>" in html
    assert "<b>3</b> compounds which contain <b>kara</b>" in html


def test_dpd_headword_every_compound_family_heading_has_jump_link() -> None:
    html = _render_compound_families({"kata": 1, "kara": 3})

    for family in ("kata", "kara"):
        assert 'href="#test_headwordcf_top"' in _family_heading(html, family)
