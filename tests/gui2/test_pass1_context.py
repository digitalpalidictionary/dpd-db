from gui2.pass1_context import (
    ANSWER_KEYS,
    AllowedValues,
    build_new_prompt,
    choose_sentences,
    related_entry_dict,
)
from db.models import DpdHeadword
from gui2.dpd_fields_lists import PASS1_FIELDS

ALLOWED = AllowedValues(
    pos=["masc", "adj"],
    pattern=["a masc", "a adj"],
    root_sign=["a", "*e"],
    root_key=[("√kam 1", "walk, go")],
)

# Real rows from Cp: the same homage line in SC and in ePitaka, with
# different case and punctuation, then three more ePitaka rows.
SC = [
    (
        "namo tassa bhagavato arahato sammāsambuddhassa. ",
        "Homage to him, the blessed one, the perfected one, the fully awakened Buddha! ",
    )
]
EPITAKA = [
    (
        "Namo tassa bhagavato arahato sammāsambuddhassa",
        "Homage to the Blessed One, the Perfected One, the Fully Self-Awakened Buddha",
    ),
    (
        "Rammā cāvesi maṃ ṭhānā, vātova dharaṇīruhaṃ ’.",
        "You send me from this lovely place, like the wind a tree growing in the earth.’",
    ),
    ("7. Kapirājacariyā", "7. The Conduct of the Monkey King"),
    (
        "Kapirājacariyaṃ sattamaṃ.",
        "The seventh, the Conduct of the Monkey King, is finished.",
    ),
]

RELATED: list[dict[str, str | int]] = [
    {"id": 1, "lemma_1": "loka 1", "pos": "masc"},
    {"id": 2, "lemma_1": "nāyaka", "pos": "masc"},
]


def test_sc_sentences_come_first() -> None:
    chosen = choose_sentences(SC, EPITAKA)
    assert chosen[0] == SC[0]


def test_never_more_than_three_sentences() -> None:
    assert len(choose_sentences(SC, EPITAKA)) == 3
    assert len(choose_sentences([], EPITAKA)) == 3


def test_same_sentence_in_sc_and_epitaka_is_sent_once() -> None:
    chosen = choose_sentences(SC, EPITAKA)
    assert [pali for pali, _ in chosen] == [
        SC[0][0],
        EPITAKA[1][0],
        EPITAKA[2][0],
    ]


def test_no_sentences_from_either_source() -> None:
    assert choose_sentences([], []) == []


def _prompt(word: str, **kwargs) -> str:
    args = {
        "word": word,
        "book": "Vimānavatthu (verse)",
        "sentences": SC,
        "related": RELATED,
        "peu": [],
        "allowed": ALLOWED,
    }
    args.update(kwargs)
    return build_new_prompt(**args)


def test_excluded_ids_leave_the_related_entries() -> None:
    prompt = _prompt("lokanāyakaṃ", exclude_ids={2})
    word_part = prompt.split("\n---\n", 1)[1]
    assert '"lemma_1": "loka 1"' in word_part
    assert "nāyaka" not in word_part.replace("lokanāyakaṃ", "")
    assert '"id"' not in word_part


def test_no_peu_block_when_peu_is_empty() -> None:
    assert "Pali English Ultimate" not in _prompt("x", peu=[])
    with_peu = _prompt("x", peu=["revatīvimāna: [Revatī+vimāna] (na) temple"])
    assert "- revatīvimāna: [Revatī+vimāna] (na) temple" in with_peu


def test_no_sentences_says_so() -> None:
    assert "No sentences found." in _prompt("x", sentences=[])


def test_fixed_part_is_the_same_for_every_word() -> None:
    # The fixed part must not change between words, or the providers'
    # prompt caches can never reuse it.
    first = _prompt("abc", sentences=SC).split("\n---\n", 1)[0]
    second = _prompt("xyz", sentences=[], related=[]).split("\n---\n", 1)[0]
    assert first == second
    assert "abc" not in first


def test_prompt_lists_answer_keys_and_real_values() -> None:
    fixed = _prompt("x").split("\n---\n", 1)[0]
    for key in ANSWER_KEYS:
        assert f'"{key}": ""' in fixed
    assert "a masc · a adj" in fixed
    assert "√kam 1 (walk, go)" in fixed
    assert "masc: masculine noun" in fixed
    assert "family_compound" not in _prompt("x")


def test_related_entries_leave_out_family_compound() -> None:
    headword = DpdHeadword(id=1, lemma_1="lokanāyaka", family_compound="loka nāyaka")
    entry = related_entry_dict(headword)
    assert "family_compound" not in entry
    assert entry["lemma_1"] == "lokanāyaka"


def test_pass1_screen_does_not_show_family_compound() -> None:
    assert "family_compound" not in PASS1_FIELDS
    assert "family_word" in PASS1_FIELDS
