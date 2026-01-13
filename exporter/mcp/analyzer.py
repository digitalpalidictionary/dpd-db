from typing import Any
from sqlalchemy.orm import Session
from db.models import DpdHeadword, Lookup
from tools.pali_alphabet import pali_alphabet
from tools.clean_machine import clean_machine

suffixes = {
    "tta"
    "tā"
    "a"
    "ā"
    "ika"
    "aka"
    "ikā"
    "ī"
    "ka"
    "aṃ"
    "ana"
    "āni"
    "o"
    "e"
    "ūni"
    "ya"
    "ena"
    "u"
    "ū"
    "āya"
    "iya"
    "*tta"
    "*tā"
    "*a"
    "*ā"
    "*ika"
    "*aka"
    "*ikā"
    "*ī"
    "*ka"
    "*aṃ"
    "*ana"
    "*āni"
    "*o"
    "*e"
    "*ūni"
    "*ya"
    "*ena"
    "*u"
    "*ū"
    "*āya"
    "*iya"
}


exceptions_list = {
    "abbrev",
    "cs",
    "letter",
    "prefix",
    "root",
    "suffix",
    "ve",
}


def tokenize_sentence(sentence: str) -> list[str]:
    """Tokenize a Pāḷi sentence and normalize to lowercase using valid Pāḷi characters."""
    pali_chars = set()
    for item in pali_alphabet:
        for char in item:
            pali_chars.add(char)
    pali_chars.add(" ")
    pali_chars.add("'")  # Allow apostrophe for sandhi

    sentence = sentence.lower()

    # Protect apostrophes using 'q' which clean_machine allows but is not in Pali
    sentence = sentence.replace("'", "q").replace("’", "q")
    sentence = clean_machine(sentence)
    sentence = sentence.replace("q", "'")

    clean_chars = [char if char in pali_chars else " " for char in sentence]
    clean_sentence = "".join(clean_chars)

    tokens = [token for token in clean_sentence.split() if token]
    return tokens


def is_pos_compatible(hw_pos: str, grammar_pos: str, grammar_string: str = "") -> bool:
    """Check if the Headword POS is compatible with the Lookup Grammar POS."""
    # Normalize
    hw_pos = hw_pos.lower()
    grammar_pos = grammar_pos.lower()
    grammar_string = grammar_string.lower()

    if hw_pos == grammar_pos:
        return True

    # Noun compatibility
    if grammar_pos == "noun" and hw_pos in ["masc", "fem", "nt"]:
        # If grammar string has specific gender, hw_pos must match
        if "masc" in grammar_string and hw_pos != "masc":
            return False
        if "fem" in grammar_string and hw_pos != "fem":
            return False
        if (
            "nt" in grammar_string and hw_pos != "nt" and "ant" not in grammar_string
        ):  # careful with 'ant' matching 'nt'
            # "ant" check is for things like "present participle" (ant) which might be in string?
            # Actually "nt" is short, could trigger false positives if grammar string is like "adjective (antonym...)"
            # But standard grammar strings are like "masc acc sg", "nt nom sg".
            # Better check for word boundary if possible, but simple check:
            # "nt" is unique enough in DPD grammar usually.
            return False
        return True

    # Adjective compatibility
    if grammar_pos == "adj" and hw_pos in ["adj"]:
        return True

    # Verb compatibility (simplified)
    # Grammar pos might be 'verb' or specific like 'pr', 'aor'
    # HW pos might be 'pr', 'aor', 'fut', etc.
    # If grammar_pos is 'verb', it likely matches any verbal pos
    # But usually lookup grammar is specific e.g. "aor 3rd sg" where pos might be "verb" or "aor"
    # Let's inspect data more if needed, but for now:
    if grammar_pos == "verb" and hw_pos in [
        "pr",
        "aor",
        "fut",
        "cond",
        "imp",
        "opt",
        "pf",
        "pp",
        "prp",
        "pfp",
        "abs",
        "inf",
        "ger",
    ]:
        # Note: pp, prp, pfp, abs, inf are often treated separately but sometimes loosely as verbs
        return True

    # Check for direct mapping or containment if unsure
    # e.g. "pp" should match "pp" (handled by equality)

    return False


def get_word_details(
    token: str,
    db_session: Session,
    from_construction: bool = False,
    grammatical: bool = True,
    is_compound_part: bool = False,
) -> list[dict[str, Any]]:
    """Helper to get word details for a given token, generating specific options based on lookup grammar."""
    lookup_entry = db_session.query(Lookup).filter(Lookup.lookup_key == token).first()
    if not lookup_entry or not lookup_entry.headwords:
        return []

    headword_ids = lookup_entry.headwords_unpack
    headwords = (
        db_session.query(DpdHeadword).filter(DpdHeadword.id.in_(headword_ids)).all()
    )

    grammar_list = lookup_entry.grammar_unpack if lookup_entry.grammar else []

    word_details = []
    for hw in headwords:
        # 1. Global Filters (Always applied)
        if "!" in hw.stem:
            continue

        # 2. Grammatical Filters (Applied if grammatical=True)
        if grammatical:
            if hw.pos in exceptions_list:
                continue
            if "(gram)" in hw.meaning_1:
                continue

        # 3. Compound Component Logic (No grammar options)
        if is_compound_part:
            entry = {
                "key": f"{hw.id}_0",
                "id": hw.id,
                "pali": token,
                "pos": hw.pos,
                "grammar": "",  # No grammar for compound parts
                "meaning_combo": hw.meaning_combo,
                "compound_type": hw.compound_type,
                "compound_construction": hw.compound_construction,
                "root_key": root_combo(hw),
                "construction": hw.construction_line1_clean,
                "components": [],
            }
            # Recursive component check
            if (
                ("comp" in hw.grammar and "in comp" not in hw.grammar)
                or "sandhi" in hw.grammar
            ) and not hw.root_key:
                # If this component is itself a compound, its parts are also compound parts
                # If it is sandhi, its parts are sandhi parts (keep grammar) - wait, instruction says "same for subpart of comp"
                # If I am a compound part, and I am a compound, my children are compound parts.
                # If I am a compound part, and I am a sandhi... this is rare in compounds.
                # Let's follow the standard logic: if "comp", passes True. If "sandhi", passes False?
                # No, if the PARENT is a compound, the child is a compound part.
                # Here 'hw' IS the component. We are looking at ITs components.

                is_sub_comp = "comp" in hw.grammar and "in comp" not in hw.grammar
                # Pass True if it is a compound breakdown
                entry["components"] = get_components_from_construction(
                    hw.construction_line1_clean,
                    db_session,
                    grammatical=grammatical,
                    is_compound_part=is_sub_comp,
                )
            word_details.append(entry)
            continue

        # 4. Standard Logic (Grammar matching)
        matched_grammar = False

        # We need to match the Headword to the Grammar entry.
        # Usually matching by lemma_clean is safest.
        if grammar_list:
            for i, (g_lemma, g_pos, g_gram) in enumerate(grammar_list):
                if g_lemma == hw.lemma_clean and is_pos_compatible(
                    hw.pos, g_pos, g_gram
                ):
                    matched_grammar = True
                    entry = {
                        "key": f"{hw.id}_{i}",  # Unique key for this specific inflection option
                        "id": hw.id,
                        "pali": token,
                        "pos": g_pos,  # Use specific pos
                        "grammar": f"{g_gram} of {g_lemma}",  # Use specific grammar with lemma
                        "meaning_combo": hw.meaning_combo,
                        "compound_type": hw.compound_type,
                        "compound_construction": hw.compound_construction,
                        "root_key": root_combo(hw),
                        "construction": hw.construction_line1_clean,
                        "components": [],
                    }
                    if (
                        ("comp" in hw.grammar and "in comp" not in hw.grammar)
                        or "sandhi" in hw.grammar
                    ) and not hw.root_key:
                        is_sub_comp = (
                            "comp" in hw.grammar and "in comp" not in hw.grammar
                        )
                        entry["components"] = get_components_from_construction(
                            hw.construction_line1_clean,
                            db_session,
                            grammatical=grammatical,
                            is_compound_part=is_sub_comp,
                        )

                    word_details.append(entry)

        # Fallback: if no specific grammar matched (or list empty), use generic headword data
        if not matched_grammar:
            # ... existing fallback code ...
            entry = {
                "key": f"{hw.id}_default",
                "id": hw.id,
                "pali": token,
                "pos": hw.pos,
                "grammar": hw.grammar,
                "meaning_combo": hw.meaning_combo,
                "compound_type": hw.compound_type,
                "compound_construction": hw.compound_construction,
                "root_key": root_combo(hw),
                "construction": hw.construction_line1_clean,
                "components": [],
            }

            if (
                ("comp" in hw.grammar and "in comp" not in hw.grammar)
                or "sandhi" in hw.grammar
            ) and not hw.root_key:
                is_sub_comp = "comp" in hw.grammar and "in comp" not in hw.grammar
                entry["components"] = get_components_from_construction(
                    hw.construction_line1_clean,
                    db_session,
                    grammatical=grammatical,
                    is_compound_part=is_sub_comp,
                )

            word_details.append(entry)

    return word_details


def get_components_from_construction(
    construction: str,
    db_session: Session,
    grammatical: bool = True,
    is_compound_part: bool = False,
) -> list[dict[str, Any]]:
    """Helper to break down a construction string into component details."""
    components = []
    parts = construction.split(" + ")
    for part in parts:
        if part not in suffixes:
            # Fetch details for the part
            part_details_list = get_word_details(
                part,
                db_session,
                from_construction=True,
                grammatical=grammatical,
                is_compound_part=is_compound_part,
            )
            if part_details_list:
                # We need to save all possible option so AI can pick which is better
                components.append(part_details_list)
            else:
                # If no details found, just add the word itself as a placeholder (wrapped in a list)
                components.append(
                    [
                        {
                            "key": f"missing_{part}",
                            "id": "",
                            "pali": part,
                            "pos": "",
                            "grammar": "in comp",
                            "meaning_combo": "",
                            "construction": "",
                        }
                    ]
                )
    return components


def analyze_sentence(
    sentence: str, db_session: Session, grammatical: bool = True
) -> list[dict[str, Any]]:
    """Analyze a Pāḷi sentence and return grammatical details for each word, including components."""
    tokens = tokenize_sentence(sentence)
    results = []

    for token in tokens:
        lookup_entry = (
            db_session.query(Lookup).filter(Lookup.lookup_key == token).first()
        )

        effective_key = token
        # Fallback for apostrophes (e.g. yo'dha -> yodha)
        if not lookup_entry and "'" in token:
            cleaned_token = token.replace("'", "")
            lookup_entry = (
                db_session.query(Lookup)
                .filter(Lookup.lookup_key == cleaned_token)
                .first()
            )
            if lookup_entry:
                effective_key = cleaned_token

        word_data = []
        status = "not_found"

        # TODO think of the way how to identify and make use of idioms

        if lookup_entry:
            # Track existing constructions from headwords to avoid duplication
            existing_constructions = set()

            # 1. Check for Headwords
            if lookup_entry.headwords:
                headword_details = get_word_details(
                    effective_key, db_session, grammatical=grammatical
                )
                word_data.extend(headword_details)

                # Collect constructions from sandhi headwords
                for item in headword_details:
                    if item["pos"] == "sandhi" and item["construction"]:
                        existing_constructions.add(item["construction"])

            # 2. Check for Deconstructor
            if lookup_entry.deconstructor:
                decons = lookup_entry.deconstructor_unpack
                for i, decon in enumerate(decons):
                    # Skip if this construction is already covered by a headword
                    if decon in existing_constructions:
                        continue

                    entry = {
                        "key": f"decon_{effective_key}_{i}",
                        "id": "",
                        "pali": effective_key,
                        "pos": "sandhi",
                        "grammar": "sandhi/compound",
                        "meaning_combo": "[Deconstructed]",
                        "compound_type": "",
                        "compound_construction": "",
                        "root_key": "",
                        "construction": decon,
                        "components": get_components_from_construction(
                            decon, db_session, grammatical=grammatical
                        ),
                    }
                    word_data.append(entry)

            if word_data:
                status = "found"

        results.append({"word": token, "status": status, "data": word_data})

    return results


def root_combo(i: DpdHeadword):
    # uniting root info into one line
    root_combo = ""
    if i.rt:
        root_combo = (
            f"{i.root_clean} {i.rt.root_group} {i.root_sign} ({i.rt.root_meaning})"
        )
    return root_combo
