from tools.tokenizer import split_sentences


def test_square_bracket_note_is_not_split():
    """Variant-reading notes are unwrapped into [square brackets] and often
    contain nikāya references like 'saṃ. ni.'. Periods inside them must not
    end a sentence."""
    text = (
        "bilaṃ bilāsayā pavisanti, dakaṃ dakāsayā "
        "[udakaṃ udakāsayā saṃ. ni. 1.2] paviṭṭhā. ataparaṃ vakkhati."
    )
    assert split_sentences(text) == [
        "bilaṃ bilāsayā pavisanti, dakaṃ dakāsayā "
        "[udakaṃ udakāsayā saṃ. ni. 1.2] paviṭṭhā. ",
        "ataparaṃ vakkhati.",
    ]


def test_round_bracket_abbreviation_is_not_split():
    """Existing behaviour: periods inside round-bracket abbreviations are
    not sentence boundaries."""
    text = (
        "pañcupādānakkhandhā āsīvisūpame (saṃ. ni. 4.238) vuttanayena "
        "daṭṭhabbā. vitthārato panettha."
    )
    assert split_sentences(text) == [
        "pañcupādānakkhandhā āsīvisūpame (saṃ. ni. 4.238) vuttanayena daṭṭhabbā. ",
        "vitthārato panettha.",
    ]


def test_nested_brackets_are_not_split():
    """Notes can contain round brackets, e.g. [... (sī. syā. kaṃ. pī.) ...].
    Nesting must keep the whole span together."""
    text = "abc (def [saṃ. ni.] ghi) jkl. mno."
    assert split_sentences(text) == ["abc (def [saṃ. ni.] ghi) jkl. ", "mno."]


def test_plain_sentences_split_on_each_mark():
    text = "ekaṃ. dve! tīṇi? cattāri; pañca."
    assert split_sentences(text) == [
        "ekaṃ. ",
        "dve! ",
        "tīṇi? ",
        "cattāri; ",
        "pañca.",
    ]


def test_unbalanced_closing_bracket_degrades_gracefully():
    """A stray closing bracket must not drive the depth negative and
    suppress later splits."""
    text = "alpha] beta. gamma."
    assert split_sentences(text) == ["alpha] beta. ", "gamma."]
