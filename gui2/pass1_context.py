"""Context and prompts for Pass1 Auto.

The sentence picker, related entries in the answer's JSON shape, the real
dictionary values, and the prompt builder. Plain inputs only,
so the prompt test (kamma thread 20261104_pass1_auto_prompt) and gui2 run
the same code."""

import json
import re
from collections.abc import Collection, Iterable
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import DpdHeadword, DpdRoot, Lookup

Sentence = tuple[str, str]  # (pali, english)

ANSWER_KEYS: tuple[str, ...] = (
    "lemma_1",
    "lemma_2",
    "pos",
    "grammar",
    "meaning_2",
    "root_key",
    "root_sign",
    "root_base",
    "family_root",
    "construction",
    "stem",
    "pattern",
    "comment",
)

SYSTEM_PROMPT = (
    "You are a Pāḷi grammarian who writes draft entries for the Digital Pāḷi "
    "Dictionary (DPD). For one Pāḷi word you return one JSON object in DPD's "
    "style. Return the JSON object only."
)

MAX_SENTENCES = 3

BOOK_NAMES: dict[str, str] = {
    "vin1&2": "Vinaya, Pārājika and Pācittiya (prose)",
    "vin-bi": "Vinaya, Bhikkhunīvibhaṅga (prose)",
    "vin3&4": "Vinaya, Mahāvagga and Cūḷavagga (prose)",
    "vin5": "Vinaya, Parivāra (prose)",
    "dn": "Dīgha Nikāya (prose)",
    "mn": "Majjhima Nikāya (prose)",
    "sn": "Saṃyutta Nikāya (prose and verse)",
    "an": "Aṅguttara Nikāya (prose)",
    "khp": "Khuddakapāṭha (prose and verse)",
    "dhp": "Dhammapada (verse)",
    "ud": "Udāna (prose and verse)",
    "iti": "Itivuttaka (prose and verse)",
    "snp": "Suttanipāta (verse)",
    "vv": "Vimānavatthu (verse)",
    "pv": "Petavatthu (verse)",
    "th": "Theragāthā (verse)",
    "thi": "Therīgāthā (verse)",
    "ap": "Apadāna (verse)",
    "bv": "Buddhavaṃsa (verse)",
    "cp": "Cariyāpiṭaka (verse)",
    "ja": "Jātaka (verse)",
    "nidd1&2": "Niddesa (commentarial prose)",
    "kva": "Kaṅkhāvitaraṇī (commentary)",
    "dhpa": "Dhammapada commentary (prose stories)",
    "jaa": "Jātaka commentary (prose stories)",
    "dna": "Dīgha Nikāya commentary",
}

POS_DESCRIPTIONS: dict[str, str] = {
    "abbrev": "abbreviation",
    "abs": "absolutive",
    "adj": "adjective",
    "aor": "aorist",
    "card": "cardinal number",
    "cond": "conditional verb",
    "cs": "conjugational sign",
    "fem": "feminine noun",
    "fut": "future verb",
    "ger": "gerund",
    "idiom": "idiomatic expression",
    "imp": "imperative verb",
    "imperf": "imperfect verb",
    "ind": "indeclinable",
    "inf": "infinitive",
    "letter": "letter of the alphabet",
    "masc": "masculine noun",
    "nt": "neuter noun",
    "opt": "optative verb",
    "ordin": "ordinal number",
    "perf": "perfect verb",
    "pp": "past participle",
    "pr": "present tense verb",
    "prefix": "prefix",
    "pron": "pronoun",
    "prp": "present participle",
    "ptp": "potential participle",
    "root": "root",
    "sandhi": "sandhi compound",
    "suffix": "suffix",
    "ve": "verbal ending",
}


def book_name(book: str) -> str:
    return BOOK_NAMES.get(book, book)


# --- sentences ---


def _sentence_key(pali: str) -> str:
    # SC and ePitaka write the same sentence with different case,
    # spacing and punctuation.
    return re.sub(r"[^a-zāīūṅñṭḍṇḷṃ]", "", pali.lower())


def choose_sentences(
    sc_sentences: Iterable[Sentence],
    epitaka_sentences: Iterable[Sentence],
    cap: int = MAX_SENTENCES,
) -> list[Sentence]:
    """SC sentences first (human translation), then ePitaka, each once."""

    chosen: list[Sentence] = []
    seen: set[str] = set()
    for pali, english in [*sc_sentences, *epitaka_sentences]:
        key = _sentence_key(pali)
        if not key or key in seen:
            continue
        seen.add(key)
        chosen.append((pali, english))
        if len(chosen) >= cap:
            break
    return chosen


# --- related entries ---


def related_headwords(db_session: Session, word: str) -> list[DpdHeadword]:
    """The headwords of the parts of the word's first two deconstructions,
    each once, in order. Same search as the old related entries."""

    headwords: list[DpdHeadword] = []
    seen: set[int] = set()
    lookups = db_session.scalars(select(Lookup).where(Lookup.lookup_key == word))
    for lookup in lookups:
        for deconstruction in lookup.deconstructor_unpack[:2]:
            for part in deconstruction.split(" + "):
                part_lookup = db_session.scalars(
                    select(Lookup).where(Lookup.lookup_key == part)
                ).first()
                if not part_lookup:
                    continue
                for headword_id in part_lookup.headwords_unpack:
                    if headword_id in seen:
                        continue
                    headword = db_session.get(DpdHeadword, headword_id)
                    if headword:
                        seen.add(headword_id)
                        headwords.append(headword)
    return headwords


def related_entry_dict(headword: DpdHeadword) -> dict[str, str | int]:
    """One headword in the answer's JSON shape, plus its id for the leak guard."""

    return {
        "id": headword.id,
        "lemma_1": headword.lemma_1,
        "lemma_2": headword.lemma_2,
        "pos": headword.pos,
        "grammar": headword.grammar,
        "meaning_2": headword.meaning_combo,
        "root_key": headword.root_key,
        "root_sign": headword.root_sign,
        "root_base": headword.root_base,
        "family_root": headword.family_root,
        "construction": headword.construction,
        "stem": headword.stem,
        "pattern": headword.pattern,
    }


# --- real dictionary values ---


@dataclass(frozen=True)
class AllowedValues:
    pos: list[str]
    pattern: list[str]
    root_sign: list[str]
    root_key: list[tuple[str, str]]  # (root, meaning)


def _by_frequency(db_session: Session, column) -> list[str]:
    rows = db_session.execute(
        select(column)
        .where(column != "")
        .group_by(column)
        .order_by(func.count().desc(), column)
    )
    return [value for (value,) in rows]


def load_allowed_values(db_session: Session) -> AllowedValues:
    """Every value the dictionary really uses for the fixed-set fields,
    most common first."""

    roots = db_session.execute(
        select(DpdRoot.root, DpdRoot.root_meaning).order_by(DpdRoot.root)
    )
    return AllowedValues(
        pos=_by_frequency(db_session, DpdHeadword.pos),
        pattern=_by_frequency(db_session, DpdHeadword.pattern),
        root_sign=_by_frequency(db_session, DpdHeadword.root_sign),
        root_key=[(root, meaning) for root, meaning in roots],
    )


# --- new prompt ---

_EXAMPLE_WORD = "lokanāyakaṃ"

# DPD entry 55988, with a comment added.
_EXAMPLE_ANSWER: dict[str, str] = {
    "lemma_1": "lokanāyaka",
    "lemma_2": "lokanāyako",
    "pos": "masc",
    "grammar": "masc, comp",
    "meaning_2": "world leader; guide to the world; master of the earth",
    "root_key": "",
    "root_sign": "",
    "root_base": "",
    "family_root": "",
    "construction": "loka + nāyaka",
    "stem": "lokanāyak",
    "pattern": "a masc",
    "comment": "An epithet of the Buddha. Accusative singular in the text.",
}

_FIELD_RULES = """\
# Field rules

## lemma_1 (the headword)
- Nouns and adjectives: the stem, without a case ending. a-stems end in -a (narena → nara), ī-stems in -ī (medhāvino → medhāvī), feminine ā-stems in -ā (vedanaṃ → vedanā), u-stems in -u (bhikkhavo → bhikkhu).
- Present, imperative, optative and future verbs: the present 3rd singular (gacchanti, gacchatu, gaccheyya, gacchissati → gacchati). The pos is then pr. Only an irregular future gets its own future headword (āhañchati, pos fut).
- Aorist: the aorist 3rd singular (upasaṅkamiṃsu → upasaṅkami).
- Participles: the masculine stem. Present participles end in -nta or -māna (vandanto → vandanta, bhuñjamāno → bhuñjamāna). Past and potential participles end in -a (nisinno → nisinna).
- Absolutives, gerunds, infinitives and indeclinables: the form as it is (gantvāna, kātave).
- An enclitic or quotation mark joined to the end (-ca, -va, -eva, -pi, -ti, -iti): leave it out and write the entry for the main word (buddhova → buddha, gacchāmīti → gacchati).
- Sandhi of two or more full words (kocañño = koci + añño): keep the form as it is. The pos is sandhi.
- A noun joined to its verb (agāramāvasati = agāraṃ + āvasati) is a compound verb. The pos is the verb's; the grammar is "pr, comp vb".

## lemma_2
- Nouns: the nominative singular (nara → naro, citta → cittaṃ, vedanā → vedanā).
- Adjectives, participles and every other part of speech: exactly lemma_1, never a nominative (pasannacitta → pasannacitta, not pasannacitto).

## pos
- Pick one from the list of real values below.
- -tvā, -tvāna, -itvā: abs. -ya, -iya, -yāna: ger. -tuṃ, -tave, -tāye: inf.
- Adverbs and all other indeclinables: ind.
- Words ending in -ādi are usually masc.

## grammar
- Compound noun or adjective: "masc, comp", "adj, comp".
- Noun or adjective made from another word: "adj, from sīla", "masc, from gāma", "nt, dimin of agāra", "fem, abstr, from mitta".
- Verbs: "pr", "pr, caus of bhavati", "aor of upasaṅkamati", "fut of āhanati".
- Other verb forms: the pos, "of", and the present 3rd singular: "prp of vandati", "pp of pasīdati", "abs of gacchati", "ger of paccavekkhati", "inf of gacchati", "abs of na paṭipucchati".
- Indeclinables: "ind, adv", "ind, prep", "ind, emph".
- Sandhi: "sandhi," and the pos of each part: "sandhi, pron + pron".

## meaning_2
- English meanings that fit the sentences, most likely first, separated by "; " (nara = man; person; human being).
- Present verbs in the 3rd singular (approaches; visits), aorists in the past (approached; drew near), futures with "will" (will attain), participles as "honouring" or "seated", absolutives as "having gone", infinitives as "to go".
- A preposition the word needs goes in brackets: "goes (to)", "goodwill (towards)".
- Proper names: "name of a mountain", "name of a river", with the story or text where it helps.
- In Vinaya texts, compounds ending in vatthu mean "case of ...".
- No explanation here. That goes in comment.

## root_key, root_sign, root_base, family_root
- These apply to words that go back to a verbal root: verbs, participles, absolutives, gerunds, infinitives, and nouns or adjectives made from them (bhikkhu, mettā).
- Leave all four empty for compounds of two or more words and for sandhi.
- root_key: pick one root from the list below, with its number (√kam 1). If no root fits, leave it empty.
- root_sign: pick one from the list below.
- root_base: for verbs and verb forms only. The root + sign > base, with (caus) or (irreg) where it applies: "√bhū + *e > bhāve (caus)", "√gam + a > gama > gaccha (irreg)". Empty for nouns and adjectives.
- family_root: the prefixes and the root, separated by spaces, without the root's number: "upa saṃ √kam", "pa √sad", "√gam".

## construction
- Pāḷi only, no English. Parts are joined with " + ".
- Compounds: the parts as they stand in the word: "loka + nāyaka", "agāraṃ + āvasati".
- Words made with a suffix: the base + the suffix: "agāra + ka", "sīla + vant", "gāma + aṇi".
- Verbs and verb forms: the prefixes + the base + the ending: "upa + saṃ + kama + ti", "bhuñja + māna", "bhāve + ti", "pa + √sad + na".
- Nouns made straight from a root: "√mar > mār + *a".
- Sandhi: the words as they stand: "koci + añño".

## stem and pattern
- pattern: pick one from the list below. Its first word is the ending of lemma_1. The stem is lemma_1 without that ending: lokanāyaka with "a masc" → "lokanāyak"; medhāvī with "ī masc" → "medhāv"; vandati with "ati pr" → "vand"; bhuñjamāna with "māna prp" → "bhuñja"; sīlavant with "ant adj" → "sīlav"; upasaṅkami with "i aor" → "upasaṅkam".
- Indeclinables, absolutives, gerunds, infinitives, sandhi and idioms: the stem is "-" and the pattern is empty.
- Use the stems and patterns of the related entries as a guide. Never use a pattern that is not in the list.

## comment
- Your own notes: how the word is used in the sentences, its case in the text, doubts, and other possible analyses.
- Keep it short. Nothing that is already in another field.
"""


def _fixed_part(allowed: AllowedValues) -> str:
    """Everything that is the same for every word. It comes first in the
    prompt, so the providers' prompt caches can reuse it."""

    skeleton = json.dumps({key: "" for key in ANSWER_KEYS}, ensure_ascii=False)
    example = json.dumps(_EXAMPLE_ANSWER, ensure_ascii=False, indent=1)
    pos_list = "\n".join(
        f"{pos}: {POS_DESCRIPTIONS[pos]}" if pos in POS_DESCRIPTIONS else pos
        for pos in allowed.pos
    )
    roots = "; ".join(f"{root} ({meaning})" for root, meaning in allowed.root_key)
    return f"""\
# Task
At the end of this message is one Pāḷi word as it appears in a text, with the sentences it occurs in and some related dictionary entries. Write a draft dictionary entry for it in the style of the Digital Pāḷi Dictionary (DPD).

# Answer
Return one JSON object with exactly these keys, in this order. Every value is a string. Use "" for a field that does not apply. No text before or after the JSON.
{skeleton}

# Example
Word in the text: {_EXAMPLE_WORD}
{example}

{_FIELD_RULES}
# Real dictionary values

## pos (pick one)
{pos_list}

## pattern (pick one, most common first)
{" · ".join(allowed.pattern)}

## root_sign (pick one, most common first)
{" · ".join(allowed.root_sign)}

## root_key (pick one; the meaning is in brackets)
{roots}
"""


def build_new_prompt(
    word: str,
    book: str,
    sentences: list[Sentence],
    related: list[dict[str, str | int]],
    peu: list[str],
    allowed: AllowedValues,
    exclude_ids: Collection[int] = (),
) -> str:
    """The fixed part, then this word's own context. `exclude_ids` removes
    headwords from the related entries (the test's leak guard)."""

    parts = [_fixed_part(allowed), "---", "# The word", f"Book: {book}"]
    parts.append(f"Word in the text: {word}")

    parts.append("\n## Sentences")
    if sentences:
        parts.append("The English may be a machine translation. Trust the Pāḷi.")
        for count, (pali, english) in enumerate(sentences, start=1):
            parts.append(f"{count}. Pāḷi: {pali}\n   English: {english}")
    else:
        parts.append("No sentences found.")

    if peu:
        parts.append("\n## Pali English Ultimate (PEU) entries")
        parts.append(
            "A guide to the split and the gender, not a source. Part of its "
            "English is machine translated. Gender codes: pu = masc, na = nt, "
            "thī = fem, ti = adj."
        )
        parts.extend(f"- {entry}" for entry in peu)

    entries = [
        {key: value for key, value in entry.items() if key != "id"}
        for entry in related
        if entry.get("id") not in exclude_ids
    ]
    if entries:
        parts.append("\n## Related dictionary entries")
        parts.append("Real DPD entries for parts of the word. Copy their style.")
        parts.extend(json.dumps(entry, ensure_ascii=False) for entry in entries)

    return "\n".join(parts) + "\n"
