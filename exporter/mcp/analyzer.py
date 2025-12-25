from typing import Any
from sqlalchemy.orm import Session
from db.models import DpdHeadword, Lookup
from tools.pali_alphabet import pali_alphabet


def tokenize_sentence(sentence: str) -> list[str]:
    """Tokenize a Pāḷi sentence and normalize to lowercase using valid Pāḷi characters."""
    pali_chars = set()
    for item in pali_alphabet:
        for char in item:
            pali_chars.add(char)
    pali_chars.add(" ")

    sentence = sentence.lower()
    clean_chars = [char if char in pali_chars else " " for char in sentence]
    clean_sentence = "".join(clean_chars)

    tokens = [token for token in clean_sentence.split() if token]
    return tokens


def analyze_sentence(sentence: str, db_session: Session) -> list[dict[str, Any]]:
    """Analyze a Pāḷi sentence and return grammatical details for each word."""
    tokens = tokenize_sentence(sentence)
    results = []

    for token in tokens:
        lookup_entry = db_session.query(Lookup).filter(Lookup.lookup_key == token).first()

        if not lookup_entry or not lookup_entry.headwords:
            results.append({
                "word": token,
                "status": "not_found",
                "details": []
            })
            continue

        headword_ids = lookup_entry.headwords_unpack
        headwords = db_session.query(DpdHeadword).filter(DpdHeadword.id.in_(headword_ids)).all()

        word_details = []
        for hw in headwords:
            word_details.append({
                "id": hw.id,
                "lemma_1": hw.lemma_1,
                "pos": hw.pos,
                "grammar": hw.grammar,
                "meaning_combo": hw.meaning_combo,
                "family_root": hw.family_root,
                "root_key": hw.root_key,
                "construction": hw.construction
            })

        results.append({
            "word": token,
            "status": "found",
            "details": word_details
        })

    return results

