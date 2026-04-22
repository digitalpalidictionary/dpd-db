# -*- coding: utf-8 -*-
"""Tests for dpd_headword.jinja Goldendict template — #192 sutta-info parity."""

# ruff: noqa: E402

import re
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


def _make_env() -> Environment:
    return Environment(
        loader=FileSystemLoader("exporter/goldendict/templates"),
        autoescape=False,
    )


def _minimal_d(su: SimpleNamespace) -> SimpleNamespace:
    """Build the minimal template context object."""
    i = SimpleNamespace(
        pos="ind",
        plus_case=None,
        meaning_combo_html="test meaning",
        degree_of_completion_html="",
        id=1,
        lemma_1="dhammavinayaṃ",
        lemma_1_="dhammavinayam",
        lemma_clean="dhammavinayam",
        lemma_link="dhammavinayam",
        lemma_ipa="",
        lemma_trad_clean="dhammavinayam",
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
        audio_male1=False,
        audio_male2=False,
        audio_female1=False,
        family_root=None,
        root_key=None,
        root_base=None,
        construction=None,
        derivative=None,
        suffix=None,
        phonetic=None,
        compound_type=None,
        compound_construction=None,
        antonym=None,
        synonym=None,
        variant=None,
        commentary=None,
        notes=None,
        cognate=None,
        link=None,
        non_ia=None,
        sanskrit=None,
    )
    return SimpleNamespace(
        header="<html><head></head>",
        i=i,
        su=su,
        construction_summary=None,
        show_id=False,
        grammar="ind",
        today="2026-04-22",
        declensions=set(),
        conjugations=set(),
        rt=SimpleNamespace(
            root_has_verb="",
            root_group="",
            root_meaning="",
            root_in_comps="",
            sanskrit_root=None,
            sanskrit_root_class="",
            sanskrit_root_meaning="",
        ),
    )


def _minimal_su(**kwargs) -> SimpleNamespace:
    """Build a SuttaInfo-like namespace with sensible defaults."""
    defaults = dict(
        cst_code=None,
        cst_nikaya=None,
        cst_book=None,
        cst_section=None,
        cst_vagga=None,
        cst_sutta=None,
        cst_paranum=None,
        cst_file=None,
        cst_m_page=None,
        cst_t_page=None,
        cst_v_page=None,
        cst_p_page=None,
        dpr_link=None,
        has_tpr=False,
        dpd_code="dn1-10",
        tpp_org=None,
        sc_code=None,
        sc_book=None,
        sc_vagga=None,
        sc_sutta=None,
        sc_eng_sutta=None,
        sc_blurb=None,
        sc_card_link=None,
        sc_vagga_link=None,
        sc_pali_link=None,
        sc_eng_link=None,
        sc_file_path=None,
        sc_github=None,
        tbw=None,
        tbw_legacy=None,
        dhamma_gift=None,
        sc_express_link=None,
        sc_voice_link=None,
        bjt_sutta_code=None,
        bjt_piṭaka=None,
        bjt_nikāya=None,
        bjt_major_section=None,
        bjt_book=None,
        bjt_minor_section=None,
        bjt_vagga=None,
        bjt_sutta=None,
        bjt_book_id=None,
        bjt_page_num=None,
        bjt_filename=None,
        bjt_github_link=None,
        bjt_web_code=None,
        bjt_tipitaka_lk_link=None,
        bjt_open_tipitaka_lk_link=None,
        dv_exists=False,
        dv_pts=None,
        dv_main_theme=None,
        dv_subtopic=None,
        dv_summary=None,
        dv_key_excerpt1=None,
        dv_key_excerpt2=None,
        dv_similes=None,
        dv_stage=None,
        dv_training=None,
        dv_aspect=None,
        dv_teacher=None,
        dv_audience=None,
        dv_method=None,
        dv_length=None,
        dv_prominence=None,
        dv_suggested_suttas=None,
        dv_parallels_exists=False,
        dv_nikayas_parallels=None,
        dv_āgamas_parallels=None,
        dv_taisho_parallels=None,
        dv_sanskrit_parallels=None,
        dv_vinaya_parallels=None,
        dv_others_parallels=None,
        is_vagga=False,
        is_samyutta=False,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _render(d: SimpleNamespace) -> str:
    env = _make_env()
    template = env.get_template("dpd_headword.jinja")
    return template.render(d=d)


class TestNormalSuttaRow:
    def test_button_label_is_sutta(self):
        su = _minimal_su(is_vagga=False, is_samyutta=False)
        html = _render(_minimal_d(su))
        assert ">sutta<" in html

    def test_sutta_fields_shown(self):
        su = _minimal_su(
            is_vagga=False,
            is_samyutta=False,
            cst_vagga="Mūlapaṇṇāsaka",
            cst_sutta="Sammādiṭṭhisutta",
            sc_vagga="Mūlapaṇṇāsaka",
            sc_sutta="sammādiṭṭhi",
            bjt_vagga="Mūlapaṇṇāsaka",
            bjt_sutta="Sammādiṭṭhisutta",
        )
        html = _render(_minimal_d(su))
        assert "Mūlapaṇṇāsaka" in html
        assert "Sammādiṭṭhisutta" in html
        assert "sammādiṭṭhi" in html

    def test_dv_catalogue_shown(self):
        su = _minimal_su(
            is_vagga=False,
            is_samyutta=False,
            dv_exists=True,
            dv_main_theme="ethics",
        )
        html = _render(_minimal_d(su))
        assert "Dhamma Vinaya Tools" in html
        assert "ethics" in html

    def test_sc_card_normal_branch(self):
        su = _minimal_su(
            is_vagga=False,
            is_samyutta=False,
            sc_code="mn1",
            sc_card_link="https://suttacentral.net/mn1",
            sc_pali_link="https://suttacentral.net/mn1/pli",
            sc_eng_link="https://suttacentral.net/mn1/en",
        )
        html = _render(_minimal_d(su))
        html_normalized = re.sub(r"\s+", " ", html)
        assert "SC Card" in html_normalized
        assert "Pāḷi Text" in html
        assert "English" in html
        assert "SC Vagga Card" not in html
        assert "SC Saṃyutta Card" not in html


class TestVaggaRow:
    def test_button_label_is_vagga(self):
        su = _minimal_su(is_vagga=True, is_samyutta=False)
        html = _render(_minimal_d(su))
        assert ">vagga<" in html

    def test_cst_sutta_hidden(self):
        su = _minimal_su(
            is_vagga=True,
            is_samyutta=False,
            cst_vagga="Sīlakkhandhavagga",
            cst_sutta="Brahmajālasutta",
        )
        html = _render(_minimal_d(su))
        assert "Sīlakkhandhavagga" in html
        assert "Brahmajālasutta" not in html

    def test_sc_sutta_and_title_hidden(self):
        su = _minimal_su(
            is_vagga=True,
            is_samyutta=False,
            sc_vagga="Sīlakkhandhavagga",
            sc_sutta="brahmajala",
            sc_eng_sutta="The All-Embracing Net of Views",
            sc_blurb="A famous sutta.",
        )
        html = _render(_minimal_d(su))
        assert "brahmajala" not in html
        assert "All-Embracing" not in html
        assert "A famous sutta" not in html

    def test_bjt_sutta_hidden(self):
        su = _minimal_su(
            is_vagga=True,
            is_samyutta=False,
            bjt_vagga="Sīlakkhandhavagga",
            bjt_sutta="Brahmajālasutta",
        )
        html = _render(_minimal_d(su))
        assert "Sīlakkhandhavagga" in html
        assert "Brahmajālasutta" not in html

    def test_dv_catalogue_hidden(self):
        su = _minimal_su(
            is_vagga=True,
            is_samyutta=False,
            dv_exists=True,
            dv_main_theme="ethics",
        )
        html = _render(_minimal_d(su))
        assert "Dhamma Vinaya Tools" not in html
        assert "ethics" not in html

    def test_sc_vagga_card_link(self):
        su = _minimal_su(
            is_vagga=True,
            is_samyutta=False,
            sc_vagga_link="https://suttacentral.net/dn-silakkhandhavagga",
            sc_pali_link="https://suttacentral.net/dn-silakkhandhavagga/pli",
            sc_eng_link="https://suttacentral.net/dn-silakkhandhavagga/en",
        )
        html = _render(_minimal_d(su))
        assert "SC Vagga Card" in html
        assert "SC Saṃyutta Card" not in html

    def test_samyuttapali_current_behavior_treated_as_vagga(self):
        su = SuttaInfo()
        su.dpd_sutta = "sagāthāvaggasaṃyuttapāḷi"
        su.dpd_code = "SN1-11"
        su.sc_code = "SN1.1"

        html = _render(_minimal_d(su))

        assert ">vagga<" in html
        assert "SC Vagga Card" in html
        assert "SC Saṃyutta Card" not in html


class TestSamyuttaRow:
    def test_button_label_is_samyutta(self):
        su = _minimal_su(is_vagga=False, is_samyutta=True)
        html = _render(_minimal_d(su))
        assert ">saṃyutta<" in html

    def test_cst_vagga_hidden(self):
        su = _minimal_su(
            is_vagga=False,
            is_samyutta=True,
            cst_vagga="Nidānasaṃyuttaṃ",
            cst_sutta="Dassanasutta",
        )
        html = _render(_minimal_d(su))
        assert "Nidānasaṃyuttaṃ" not in html
        assert "Dassanasutta" not in html

    def test_sc_vagga_hidden(self):
        su = _minimal_su(
            is_vagga=False,
            is_samyutta=True,
            sc_vagga="Nidānasaṃyutta",
            sc_sutta="dassana",
        )
        html = _render(_minimal_d(su))
        assert "Nidānasaṃyutta" not in html
        assert "dassana" not in html

    def test_bjt_vagga_hidden(self):
        su = _minimal_su(
            is_vagga=False,
            is_samyutta=True,
            bjt_vagga="Nidānasaṃyuttaṃ",
            bjt_sutta="Dassanasutta",
        )
        html = _render(_minimal_d(su))
        assert "Nidānasaṃyuttaṃ" not in html
        assert "Dassanasutta" not in html

    def test_dv_catalogue_hidden(self):
        su = _minimal_su(
            is_vagga=False,
            is_samyutta=True,
            dv_exists=True,
            dv_main_theme="dependent origination",
        )
        html = _render(_minimal_d(su))
        assert "Dhamma Vinaya Tools" not in html
        assert "dependent origination" not in html

    def test_sc_samyutta_card_link(self):
        su = _minimal_su(
            is_vagga=False,
            is_samyutta=True,
            sc_vagga_link="https://suttacentral.net/sn12",
        )
        html = _render(_minimal_d(su))
        assert "SC Saṃyutta Card" in html
        assert "SC Vagga Card" not in html

    def test_sc_eng_sutta_and_blurb_hidden(self):
        su = _minimal_su(
            is_vagga=False,
            is_samyutta=True,
            sc_eng_sutta="Linked Discourses on Causality",
            sc_blurb="Contains discourses on dependent origination.",
        )
        html = _render(_minimal_d(su))
        assert "Linked Discourses on Causality" not in html
        assert "Contains discourses" not in html
