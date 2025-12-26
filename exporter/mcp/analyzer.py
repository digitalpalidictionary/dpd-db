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


def get_word_details(token: str, db_session: Session) -> list[dict[str, Any]]:
    """Helper to get word details for a given token."""
    lookup_entry = db_session.query(Lookup).filter(Lookup.lookup_key == token).first()
    if not lookup_entry or not lookup_entry.headwords:
        return []

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
            "family_compound": hw.family_compound,
            "compound_type": hw.compound_type,
            "root_key": hw.root_key,
            "construction": hw.construction
        })
    return word_details


def analyze_sentence(sentence: str, db_session: Session) -> list[dict[str, Any]]:
    """Analyze a Pāḷi sentence and return grammatical details for each word, including components."""
    tokens = tokenize_sentence(sentence)
    results = []

    for token in tokens:
        lookup_entry = db_session.query(Lookup).filter(Lookup.lookup_key == token).first()

        word_details = get_word_details(token, db_session)
        deconstructor_output = []
        status = "not_found"
        components = {}

        if lookup_entry:
            deconstructor_output = lookup_entry.deconstructor_unpack
            
            # Find components from deconstructor
            for decon in deconstructor_output:
                parts = [p.strip() for p in decon.split("+")]
                for part in parts:
                    if part not in components and part != token:
                        part_details = get_word_details(part, db_session)
                        if part_details:
                            components[part] = part_details

            # Find components from headword construction if it's a compound
            for hw in word_details:
                if " + " in hw["construction"]:
                    parts = [p.strip() for p in hw["construction"].split("+")]
                    for part in parts:
                        # Clean part if it contains roots (√) or other markers
                        clean_part = part.replace("√", "").strip()
                        if clean_part and clean_part not in components and clean_part != token:
                            part_details = get_word_details(clean_part, db_session)
                            if part_details:
                                components[clean_part] = part_details

            if word_details or deconstructor_output:
                status = "found"

        results.append({
            "word": token,
            "status": status,
            "deconstructor": deconstructor_output,
            "details": word_details,
            "components": components
        })

    return results

