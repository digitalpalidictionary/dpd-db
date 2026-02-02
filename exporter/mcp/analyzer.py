from typing import Any
from sqlalchemy.orm import Session
from db.models import DpdHeadword, Lookup
from tools.pali_alphabet import pali_alphabet
from tools.clean_machine import clean_machine

suffixes = {
    "tta",
    "tā",
    "a",
    "ā",
    "ika",
    "aka",
    "ikā",
    "ī",
    "ka",
    "aṃ",
    "ana",
    "āni",
    "o",
    "e",
    "ūni",
    "ya",
    "ena",
    "u",
    "ū",
    "āya",
    "iya",
    "*tta",
    "*tā",
    "*a",
    "*ā",
    "*ika",
    "*aka",
    "*ikā",
    "*ī",
    "*ka",
    "*aṃ",
    "*ana",
    "*āni",
    "*o",
    "*e",
    "*ūni",
    "*ya",
    "*ena",
    "*u",
    "*ū",
    "*āya",
    "*iya",
}

exceptions_list = {
    "cs",
    "letter",
    "prefix",
    "root",
    "suffix",
    "ve",
}

exceptions_comp = {
    "abbrev",
}

sandhi_particles = {" + api", " + ca", " + eva", " + iti", " + iva", " + hi"}

case_keywords = {
    "nom",
    "acc",
    "gen",
    "dat",
    "instr",
    "ins",
    "abl",
    "loc",
    "voc",
    "sg",
    "pl",
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
        if "masc " in grammar_string and hw_pos != "masc":
            return False
        if "fem " in grammar_string and hw_pos != "fem":
            return False
        if "nt " in grammar_string and hw_pos != "nt":
            return False
        return True

    # Adjective compatibility
    if grammar_pos == "adj" and hw_pos in ["adj"]:
        return True

    # Verb compatibility (simplified)
    if grammar_pos == "verb" and hw_pos in [
        "pr",
        "aor",
        "fut",
        "cond",
        "imp",
        "opt",
        "pp",
        "prp",
        "abs",
        "inf",
        "ger",
    ]:
        return True

    return False


def is_stem_compatible(grammar_string: str) -> bool:
    """Check if a grammar string represents a stem or uninflected form."""
    g = grammar_string.lower()
    if "in comp" in g:
        return True

    # If it contains any case/number keyword, it is likely inflected, not a pure stem
    tokens = g.split()
    for t in tokens:
        if t in case_keywords:
            return False

    return True


def get_word_details(
    token: str,
    db_session: Session,
    from_construction: bool = False,
    grammatical: bool = False,
    is_compound_part: bool = False,
    is_inflected_part: bool = True,
) -> list[dict[str, Any]]:
    """Helper to get word details for a given token, generating specific options based on lookup grammar."""
    if token == "sati":
        print(f"DEBUG: get_word_details('sati', is_inflected_part={is_inflected_part})")

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

        # 2. Compound/Sandhi Part Filters
        if from_construction and hw.pos in exceptions_comp:
            continue

        # 3. Grammatical Filters (Applied if grammatical=False)
        if not grammatical:
            if hw.pos in exceptions_list:
                continue
            if "(gram)" in hw.meaning_1:
                continue

        # 4. Compound Component Logic (No grammar options)
        # Only use this simplified block if it is NOT an inflected part (i.e. it's a stem)
        if is_compound_part and not is_inflected_part:
            # Stem Filter: Check if this headword is a valid stem for the token
            is_valid_stem = False
            if grammar_list:
                for i, (g_lemma, g_pos, g_gram) in enumerate(grammar_list):
                    if g_lemma == hw.lemma_clean and is_stem_compatible(g_gram):
                        is_valid_stem = True
                        break

            if not is_valid_stem and hw.lemma_clean == token:
                is_valid_stem = True

            if not is_valid_stem and not grammar_list:
                is_valid_stem = True

            if not is_valid_stem:
                continue

            score, completeness = get_completeness(hw)
            entry = {
                "key": f"{hw.id}_0",
                "id": hw.id,
                "lemma": hw.lemma_1,
                "degree_of_completion": completeness,
                "score": score,
                "pali": token,
                "pos": hw.pos,
                "grammar": "",  # No grammar for compound parts
                "meaning_combo": hw.meaning_combo,
                "compound_type": hw.compound_type,
                "compound_construction": hw.compound_construction,
                "root_key": root_combo(hw),
                "construction": hw.construction_summary,
                "components": [],
            }
            # Recursive component check
            is_comp_vb = "comp vb" in hw.grammar or hw.pos == "comp vb"
            if (
                ("comp" in hw.grammar and "in comp" not in hw.grammar)
                or "sandhi" in hw.grammar
                or is_comp_vb
            ) and not hw.root_key:
                is_sub_comp = (
                    "comp" in hw.grammar
                    and "in comp" not in hw.grammar
                    and not is_comp_vb
                )

                # Determine breakdown source based on compound type
                breakdown_source = hw.construction_summary
                force_inflected = False

                ct = hw.compound_type.lower()
                if "dvanda" in ct:
                    breakdown_source = hw.construction_summary
                elif any(
                    x in ct
                    for x in ["abyayībhāva", "tappurisa", "digu", "kammadhāraya"]
                ):
                    if hw.compound_construction:
                        breakdown_source = hw.compound_construction
                else:
                    # Fallback/Default behavior
                    if hw.compound_construction:
                        clean_comp_const = hw.compound_construction.replace(
                            "<b>", ""
                        ).replace("</b>", "")
                        if clean_comp_const.strip():
                            breakdown_source = hw.compound_construction

                # Sandhi and Comp VB are treated as inflected contexts
                if "sandhi" in hw.grammar or is_comp_vb:
                    force_inflected = True

                # Pass True if it is a compound breakdown
                entry["components"] = get_components_from_construction(
                    breakdown_source,
                    db_session,
                    grammatical=grammatical,
                    is_compound_part=is_sub_comp,
                    force_inflected=force_inflected,
                )
            word_details.append(entry)
            continue

        # 4. Standard Logic (Grammar matching)
        matched_grammar = False

        score, completeness = get_completeness(hw)

        # Calculate components once per headword to avoid redundancy
        hw_components = []
        is_comp_vb = "comp vb" in hw.grammar or hw.pos == "comp vb"

        if (
            ("comp" in hw.grammar and "in comp" not in hw.grammar)
            or "sandhi" in hw.grammar
            or is_comp_vb
        ) and not hw.root_key:
            is_sub_comp = (
                "comp" in hw.grammar and "in comp" not in hw.grammar and not is_comp_vb
            )

            # Determine breakdown source based on compound type
            breakdown_source = hw.construction_summary
            force_inflected = False

            ct = hw.compound_type.lower()
            if "dvanda" in ct:
                breakdown_source = hw.construction_summary
            elif any(
                x in ct for x in ["abyayībhāva", "tappurisa", "digu", "kammadhāraya"]
            ):
                if hw.compound_construction:
                    breakdown_source = hw.compound_construction
            else:
                # Fallback/Default behavior
                if hw.compound_construction:
                    clean_comp_const = hw.compound_construction.replace(
                        "<b>", ""
                    ).replace("</b>", "")
                    if clean_comp_const.strip():
                        breakdown_source = hw.compound_construction

            # Sandhi and Comp VB are treated as inflected contexts
            if "sandhi" in hw.grammar or is_comp_vb:
                force_inflected = True

            if "ānāpānassati" in hw.lemma_1:
                print(f"DEBUG: Analyzing components for {hw.lemma_1}")
                print(f"  grammar: '{hw.grammar}'")
                print(f"  force_inflected: {force_inflected}")

            hw_components = get_components_from_construction(
                breakdown_source,
                db_session,
                grammatical=grammatical,
                is_compound_part=is_sub_comp,
                force_inflected=force_inflected,
            )

        # We need to match the Headword to the Grammar entry.
        # Usually matching by lemma_clean is safest.

        if is_inflected_part:
            # Standard Logic: Match exact grammar
            if grammar_list:
                for i, (g_lemma, g_pos, g_gram) in enumerate(grammar_list):
                    if g_lemma == hw.lemma_clean and is_pos_compatible(
                        hw.pos, g_pos, g_gram
                    ):
                        matched_grammar = True
                        entry = {
                            "key": f"{hw.id}_{i}",
                            "id": hw.id,
                            "lemma": hw.lemma_1,
                            "degree_of_completion": completeness,
                            "score": score,
                            "pali": token,
                            "pos": g_pos,
                            "grammar": f"{g_gram} of {g_lemma}",
                            "meaning_combo": hw.meaning_combo,
                            "compound_type": hw.compound_type,
                            "compound_construction": hw.compound_construction,
                            "root_key": root_combo(hw),
                            "construction": hw.construction_summary,
                            "components": hw_components,
                        }
                        word_details.append(entry)

            # Fallback for inflected parts if no grammar matched
            if not matched_grammar:
                entry = {
                    "key": f"{hw.id}_default",
                    "id": hw.id,
                    "lemma": hw.lemma_1,
                    "degree_of_completion": completeness,
                    "score": score,
                    "pali": token,
                    "pos": hw.pos,
                    "grammar": hw.grammar,
                    "meaning_combo": hw.meaning_combo,
                    "compound_type": hw.compound_type,
                    "compound_construction": hw.compound_construction,
                    "root_key": root_combo(hw),
                    "construction": hw.construction_summary,
                    "components": hw_components,
                }
                word_details.append(entry)

        else:
            # Stem/Uninflected Logic (is_inflected_part=False)
            # Only include if the headword can be a stem (e.g. "in comp" or no case info)
            is_valid_stem = False

            if grammar_list:
                for i, (g_lemma, g_pos, g_gram) in enumerate(grammar_list):
                    if g_lemma == hw.lemma_clean and is_stem_compatible(g_gram):
                        if token == "sati":
                            print(
                                f"DEBUG: Accepted stem {hw.lemma_clean} for {token} via grammar: {g_gram}"
                            )
                        is_valid_stem = True
                        break

            # Additional check: if lemma matches token, it's highly likely a valid stem usage
            if not is_valid_stem and hw.lemma_clean == token:
                if token == "sati":
                    print(
                        f"DEBUG: Accepted stem {hw.lemma_clean} for {token} via strict lemma match"
                    )
                is_valid_stem = True

            # Fallback: if no grammar list at all exists in lookup for this token, assume valid
            if not is_valid_stem and not grammar_list:
                is_valid_stem = True

            if is_valid_stem:
                entry = {
                    "key": f"{hw.id}_default",
                    "id": hw.id,
                    "lemma": hw.lemma_1,
                    "degree_of_completion": completeness,
                    "score": score,
                    "pali": token,
                    "pos": hw.pos,
                    "grammar": "",  # Stems don't show grammar
                    "meaning_combo": hw.meaning_combo,
                    "compound_type": hw.compound_type,
                    "compound_construction": hw.compound_construction,
                    "root_key": root_combo(hw),
                    "construction": hw.construction_summary,
                    "components": hw_components,
                }
                word_details.append(entry)

    # Sort results by completeness (desc) and lemma (asc)
    word_details.sort(key=lambda x: (-x["score"], x["lemma"]))

    return word_details


def get_completeness(i: DpdHeadword):
    """
    Return score and string for degree of completion.
    2: complete = meaning_1 and source_1
    1: semi-complete = meaning_1 and no source_1
    0: incomplete = no meaning_1
    """
    if i.meaning_1:
        if i.source_1:
            return 2, "complete"
        else:
            return 1, "semi-complete"
    else:
        return 0, "incomplete"


def get_components_from_construction(
    construction: str,
    db_session: Session,
    grammatical: bool = False,
    is_compound_part: bool = False,
    force_inflected: bool = False,
) -> list[dict[str, Any]]:
    """Helper to break down a construction string into component details."""
    components = []
    parts = construction.split(" + ")
    for part in parts:
        # Determine if this specific part needs grammatical analysis (inflected)
        is_inflected = force_inflected
        clean_part = part

        if "<b>" in part:
            clean_part = part.replace("<b>", "").replace("</b>", "")
            # If the part was bolded in a compound construction, it implies inflected form
            is_inflected = True
        else:
            clean_part = part.replace("<b>", "").replace("</b>", "")

        if clean_part not in suffixes:
            # Fetch details for the part
            part_details_list = get_word_details(
                clean_part,
                db_session,
                from_construction=True,
                grammatical=grammatical,
                is_compound_part=is_compound_part,
                is_inflected_part=is_inflected,
            )
            if part_details_list:
                # We need to save all possible option so AI can pick which is better
                components.append(part_details_list)
            else:
                # If no details found, just add the word itself as a placeholder (wrapped in a list)
                components.append(
                    [
                        {
                            "key": f"missing_{clean_part}",
                            "id": "",
                            "pali": clean_part,
                            "pos": "",
                            "grammar": "in comp",
                            "meaning_combo": "",
                            "construction": "",
                        }
                    ]
                )
    return components


def analyze_sentence(
    sentence: str, db_session: Session, grammatical: bool = False
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

                # Special Check: If deconstructor has particle sandhi (e.g. "word + api")
                # and NO headword is "sandhi", then these headwords are likely just the base word
                # added by scripts/build/api_ca_eva_iti_iva_hi.py and should be skipped.
                skip_headwords = False
                if lookup_entry.deconstructor:
                    has_sandhi_headword = any(
                        item["pos"] == "sandhi" for item in headword_details
                    )
                    if not has_sandhi_headword:
                        decons = lookup_entry.deconstructor_unpack
                        for d in decons:
                            if any(d.endswith(p) for p in sandhi_particles):
                                skip_headwords = True
                                break

                if not skip_headwords:
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
                            decon,
                            db_session,
                            grammatical=grammatical,
                            force_inflected=True,
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
