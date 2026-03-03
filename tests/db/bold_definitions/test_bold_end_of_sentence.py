from bs4 import BeautifulSoup
from db.bold_definitions.functions import get_bold_strings


def test_bold_at_end_of_paragraph_logic():
    """
    Test the extraction logic for a bold word at the very end of a paragraph.
    The current script (Phase 2) would skip this because of 'if bold.next_sibling is not None'.
    """
    html = '<p>vande <hi rend="bold">sugataṃ</hi></p>'
    soup = BeautifulSoup(html, "xml")
    para = soup.p
    bold = para.find("hi", rend="bold")

    # In Phase 2, this is None, causing the skip.
    assert bold.next_sibling is None

    # We want get_bold_strings to handle this gracefully (bold_n should be empty)
    bold_clean, bold_e, bold_comp, bold_n = get_bold_strings(bold)

    assert bold_clean == "sugataṃ"
    assert bold_n == ""
    assert bold_e == ""
    # bold_comp should still contain the bold text
    assert "<b>sugataṃ</b>" in bold_comp


def test_bold_with_punctuation_at_end():
    """
    Test bold word followed by punctuation inside the tag, at end of paragraph.
    """
    html = '<p>vande <hi rend="bold">dhammaṃ.</hi></p>'
    soup = BeautifulSoup(html, "xml")
    para = soup.p
    bold = para.find("hi", rend="bold")

    assert bold.next_sibling is None

    bold_clean, bold_e, bold_comp, bold_n = get_bold_strings(bold)

    # Note: text_cleaner might change "dhammaṃ." to "dhammaṃ" or keep punctuation.
    # The current text_cleaner lowers it and replaces some things.
    assert "dhammaṃ" in bold_clean
    assert bold_n == ""


def test_bold_followed_by_punctuation_outside():
    """
    Test bold word followed by punctuation outside the tag, at end of paragraph.
    """
    html = '<p>vande <hi rend="bold">saṅghaṃ</hi>.</p>'
    soup = BeautifulSoup(html, "xml")
    para = soup.p
    bold = para.find("hi", rend="bold")

    # This DOES have a next sibling (".")
    assert bold.next_sibling is not None

    bold_clean, bold_e, bold_comp, bold_n = get_bold_strings(bold)
    assert bold_clean == "saṅghaṃ"
    # It seems the original logic clears a single dot in bold_n via useless_beginnings
    assert bold_n == ""
    assert bold_e == ""
