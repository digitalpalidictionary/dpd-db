#!/usr/bin/env python3


from tools.sutta_name_cleaning import clean_bjt_sutta, clean_sc_sutta


class TestCleanScSutta:
    def test_trailing_niggahita_stripped(self):
        assert clean_sc_sutta("Mettāsuttaṃ") == "mettāsutta"

    def test_no_niggahita_unchanged(self):
        assert clean_sc_sutta("Mettāsutta") == "mettāsutta"

    def test_empty_string(self):
        assert clean_sc_sutta("") == ""

    def test_whitespace_only(self):
        assert clean_sc_sutta("   ") == ""

    def test_whitespace_trimmed(self):
        assert clean_sc_sutta("  Mettāsutta  ") == "mettāsutta"

    def test_mid_string_niggahita_untouched(self):
        assert clean_sc_sutta("Saṃyuttanikāya") == "saṃyuttanikāya"

    def test_trailing_niggahita_with_whitespace(self):
        assert clean_sc_sutta("  Mettāsuttaṃ  ") == "mettāsutta"

    def test_lowercased(self):
        assert clean_sc_sutta("BRAHMAJĀLASUTTA") == "brahmajālasutta"

    def test_dot_above_m_converted(self):
        assert clean_sc_sutta("Dhammasaṁgīti") == "dhammasaṃgīti"

    def test_dot_above_m_trailing_stripped(self):
        assert clean_sc_sutta("Suttaṁ") == "sutta"

    def test_leading_number_dot_space_stripped(self):
        assert (
            clean_sc_sutta("10. Tiladakkhiṇavimānavatthu") == "tiladakkhiṇavimānavatthu"
        )

    def test_trailing_parenthetical_stripped(self):
        assert clean_sc_sutta("Kapilasutta (dhammacariyasutta)") == "kapilasutta"

    def test_leading_parenthetical_stripped(self):
        assert (
            clean_sc_sutta("(Paṭhama) Devasabhattheragāthā") == "devasabhattheragāthā"
        )

    def test_mid_parenthetical_stripped(self):
        assert clean_sc_sutta("Dhamma (nāvā) sutta") == "dhamma sutta"

    def test_leading_number_and_parenthetical(self):
        assert clean_sc_sutta("10. (Uttara) Pāyāsivimānavatthu") == "pāyāsivimānavatthu"

    def test_leading_number_no_dot(self):
        assert clean_sc_sutta("5 Cūḷasutasomajātaka") == "cūḷasutasomajātaka"

    def test_square_brackets_stripped(self):
        assert clean_sc_sutta("[dutiyaambasutta]") == ""

    def test_square_brackets_inline(self):
        assert clean_sc_sutta("Dutiya[foo]ambasutta") == "dutiyaambasutta"


class TestCleanBjtSutta:
    def test_trailing_niggahita_stripped(self):
        assert clean_bjt_sutta("Mettāsuttaṃ") == "mettāsutta"

    def test_no_niggahita_unchanged(self):
        assert clean_bjt_sutta("Mettāsutta") == "mettāsutta"

    def test_empty_string(self):
        assert clean_bjt_sutta("") == ""

    def test_whitespace_only(self):
        assert clean_bjt_sutta("   ") == ""

    def test_leading_number_dot_space_stripped(self):
        assert clean_bjt_sutta("12. Mettāsutta") == "mettāsutta"

    def test_leading_single_digit_stripped(self):
        assert clean_bjt_sutta("5.Foo") == "foo"

    def test_leading_number_and_trailing_niggahita(self):
        assert clean_bjt_sutta("12. Mettāsuttaṃ") == "mettāsutta"

    def test_whitespace_trimmed(self):
        assert clean_bjt_sutta("  Mettāsutta  ") == "mettāsutta"

    def test_mid_string_niggahita_untouched(self):
        assert clean_bjt_sutta("Saṃyuttanikāya") == "saṃyuttanikāya"

    def test_lowercased(self):
        assert clean_bjt_sutta("12. BRAHMAJĀLASUTTA") == "brahmajālasutta"
