# ruff: noqa: E402

import sys
import types
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader

sys.modules.setdefault(
    "aksharamukha",
    types.SimpleNamespace(
        transliterate=types.SimpleNamespace(process=lambda *args, **kwargs: "")
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


def _render_template(su: SuttaInfo) -> str:
    env = Environment(
        loader=FileSystemLoader("exporter/webapp/templates"), autoescape=False
    )
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
