"""Bolding utilities for inserting <b> tags around matched Pāḷi word forms in verse text."""

import re
from typing import Any

from sqlalchemy.orm import Session

from db.models import DpdHeadword
from tools.speech_marks import SpeechMarkManager
from tools.speech_marks_replacement import replace_speech_marks


def _get_db_inflections(
    headword_id: int,
    db_session: Session,
) -> list[str]:
    """Return database inflections for a headword, longest forms first."""
    try:
        headword = db_session.query(DpdHeadword).filter_by(id=headword_id).first()
    except Exception:
        return []
    if not headword:
        return []

    inflections = {
        inflection
        for inflection in headword.inflections_list
        if inflection and inflection.strip()
    }
    return sorted(inflections, key=len, reverse=True)


def _verse_tokens(verse_text: str) -> list[str]:
    """Return word-like tokens from verse text, preserving apostrophes."""
    tokens: list[str] = []
    token_chars: list[str] = []
    for char in verse_text:
        if char.isalpha() or char == "'":
            token_chars.append(char)
            continue
        if token_chars:
            tokens.append("".join(token_chars))
            token_chars = []
    if token_chars:
        tokens.append("".join(token_chars))
    return tokens


def _find_verse_token_from_inflections(
    verse_text: str,
    inflections: list[str],
) -> str | None:
    """Find the first verse token containing a database inflection."""
    for token in _verse_tokens(verse_text):
        for inflection in inflections:
            if inflection in token:
                return token
    return None


def _matches_full_left_side(component_pali: str, left_side: str) -> bool:
    """Return true when left_side is an inflected spelling of component_pali."""
    endings = "aāiīuūeoṃ"
    return component_pali.rstrip(endings) == left_side.rstrip(endings)


def strip_bold_tags(text: str) -> str:
    """Remove <b> and </b> tags from text."""
    return re.sub(r"</?b>", "", text)


def find_token_in_apos_verse(token: str, verse: str) -> str:
    """Find the apostrophe-containing form of a token as it appears in the verse.

    Scans the verse ignoring apostrophe characters to match the token, then returns
    the corresponding substring which may include apostrophes.
    """
    n = len(verse)
    tok_len = len(token)
    for start in range(n):
        j = 0
        k = start
        while k < n and j < tok_len:
            if verse[k] == "'":
                k += 1
                continue
            if verse[k] == token[j]:
                j += 1
                k += 1
            else:
                break
        if j == tok_len:
            return verse[start:k]
    return token


def bold_component_in_token(
    apos_token: str,
    component_pali: str,
    headword_id: int,
    db_session: Session,
    is_first_component: bool = False,
) -> str:
    """Bold component_pali within apos_token using actual inflections from DpdHeadword.

    For first component: bold only the component itself.
    For non-first components: if found form has a suffix in the token (more text follows),
    bold only the found form; otherwise bold to end of token.

    This position check handles nested compounds correctly: a component that is 'last'
    within its sub-compound may still have a suffix in the full verse token.

    Strategy (in order):
    0. Try database inflections from DpdHeadword(headword_id), longest first.
    1. Try component_pali directly found in apos_token.
    2. For sandhi (apostrophe in token): bold left or right side.
    3. Direct substring match.
    4. Fallback: bold the whole token.
    """

    # 0. Prefer database inflections, longest first.
    inflections = _get_db_inflections(headword_id, db_session)
    for inflection in inflections:
        if inflection in apos_token:
            if "'" in apos_token:
                left, _, right = apos_token.partition("'")
                if inflection in left:
                    idx = left.index(inflection)
                    end = idx + len(inflection)
                    if (
                        is_first_component
                        and idx == 0
                        and end < len(left)
                        and _matches_full_left_side(component_pali, left)
                    ):
                        return "<b>" + left + "</b>'" + right
                    return (
                        left[:idx]
                        + "<b>"
                        + left[idx:end]
                        + "</b>"
                        + left[end:]
                        + "'"
                        + right
                    )
                else:
                    idx = right.index(inflection)
                    end = idx + len(inflection)
                    return (
                        left
                        + "'"
                        + right[:idx]
                        + "<b>"
                        + right[idx:end]
                        + "</b>"
                        + right[end:]
                    )
            else:
                idx = apos_token.index(inflection)
                end = idx + len(inflection)
                has_suffix = end < len(apos_token)
                if is_first_component or has_suffix:
                    return (
                        apos_token[:idx]
                        + "<b>"
                        + inflection
                        + "</b>"
                        + apos_token[end:]
                    )
                else:
                    return apos_token[:idx] + "<b>" + apos_token[idx:] + "</b>"

    # 1. Exact match fallback.
    if component_pali in apos_token:
        if "'" in apos_token:
            left, _, right = apos_token.partition("'")
            if component_pali in left:
                idx = left.index(component_pali)
                end = idx + len(component_pali)
                return (
                    left[:idx]
                    + "<b>"
                    + left[idx:end]
                    + "</b>"
                    + left[end:]
                    + "'"
                    + right
                )
            else:
                idx = right.index(component_pali)
                end = idx + len(component_pali)
                return (
                    left
                    + "'"
                    + right[:idx]
                    + "<b>"
                    + right[idx:end]
                    + "</b>"
                    + right[end:]
                )
        else:
            idx = apos_token.index(component_pali)
            end = idx + len(component_pali)
            has_suffix = end < len(apos_token)
            if is_first_component or has_suffix:
                return (
                    apos_token[:idx]
                    + "<b>"
                    + component_pali
                    + "</b>"
                    + apos_token[end:]
                )
            else:
                return apos_token[:idx] + "<b>" + apos_token[idx:] + "</b>"

    # 2. Apostrophe-split fallback for sandhi where no database inflection matches
    if "'" in apos_token:
        left, _, right = apos_token.partition("'")
        pali_no_m = component_pali.rstrip("ṃ")
        pali_norm = pali_no_m.rstrip("aāiīuūeo")
        if pali_norm and (left.startswith(pali_norm) or pali_norm.startswith(left)):
            return f"<b>{left}</b>'{right}"
        return f"{left}'<b>{right}</b>"

    # 3. Direct match (fallback if inflections not found)
    if component_pali in apos_token:
        idx = apos_token.index(component_pali)
        end = idx + len(component_pali)
        has_suffix = end < len(apos_token)
        if is_first_component or has_suffix:
            return apos_token.replace(component_pali, f"<b>{component_pali}</b>", 1)
        else:
            return apos_token[:idx] + "<b>" + apos_token[idx:] + "</b>"

    # 4. Strip final ṃ and try
    pali_no_m = component_pali.rstrip("ṃ")
    if len(pali_no_m) > 1 and pali_no_m in apos_token:
        idx = apos_token.index(pali_no_m)
        end = idx + len(pali_no_m)
        has_suffix = end < len(apos_token)
        if is_first_component or has_suffix:
            return apos_token.replace(pali_no_m, f"<b>{pali_no_m}</b>", 1)
        else:
            return apos_token[:idx] + "<b>" + apos_token[idx:] + "</b>"

    # 5. Stem match: strip trailing short vowel, bold from stem position
    stem = component_pali.rstrip("aāiīuūeo")
    if len(stem) > 1 and stem in apos_token:
        idx = apos_token.index(stem)
        end = min(idx + len(component_pali), len(apos_token))
        has_suffix = end < len(apos_token)
        if is_first_component or has_suffix:
            return (
                apos_token[:idx]
                + "<b>"
                + apos_token[idx:end]
                + "</b>"
                + apos_token[end:]
            )
        else:
            return apos_token[:idx] + "<b>" + apos_token[idx:] + "</b>"

    # 6. Fallback: bold whole token
    return f"<b>{apos_token}</b>"


def bold_word_toplevel(apos_token: str) -> str:
    """Bold the entire token for a top-level (non-component) word."""
    return f"<b>{apos_token}</b>"


def bold_word_in_verse(
    verse_text: str,
    apos_token: str,
    component_pali: str,
    headword_id: int,
    db_session: Session,
    is_first_component: bool = False,
    is_top_level: bool = False,
) -> str:
    """Bold component_pali in apos_token, then replace apos_token in verse_text."""
    if apos_token not in _verse_tokens(verse_text):
        inflections = _get_db_inflections(headword_id, db_session)
        verse_token = _find_verse_token_from_inflections(verse_text, inflections)
        if verse_token:
            apos_token = verse_token

    if is_top_level:
        bolded_token = bold_word_toplevel(apos_token)
    else:
        bolded_token = bold_component_in_token(
            apos_token, component_pali, headword_id, db_session, is_first_component
        )
    escaped_token = re.escape(apos_token)
    pattern = rf"(?<![a-zA-Zāīūḍḷṅñṇṃśṣ])({escaped_token})(?![a-zA-Zāīūḍḷṅñṇṃśṣ])"
    return re.sub(pattern, bolded_token, verse_text)


def collect_all_ids(
    option: dict[str, Any], word_in_verse: str, component_index: int = 0, depth: int = 0
) -> list[tuple[int, str, str, bool, bool]]:
    """Recursively collect (headword_id, component_pali, word_in_verse, is_first_component, is_top_level) from an option tree.

    Traverses all nested components. Skips decon_ keys and empty IDs at every level.
    is_first_component is True if this component is the first in a child compound (depth > 0 and component_index == 0).
    is_top_level is True for entries at depth=0 (standalone top-level words, not compound parts).
    """
    results: list[tuple[int, str, str, bool, bool]] = []

    hw_id = option.get("id")
    key = option.get("key", "")
    pali = option.get("pali", word_in_verse)

    # Only set is_first=True for first component of child compounds, not top-level
    is_first = component_index == 0 and depth > 0
    is_top_level = depth == 0
    if hw_id and not key.startswith("decon_"):
        results.append((int(hw_id), pali, word_in_verse, is_first, is_top_level))

    should_recurse = (
        option.get("compound_type", "")
        or option.get("pos", "") in {"sandhi", "sandhi/compound"}
        or key.startswith("decon_")
    )
    if should_recurse:
        components_list = option.get("components", [])
        for i, comp_list in enumerate(components_list):
            if not comp_list:
                continue
            best_comp = max(comp_list, key=lambda x: x.get("ai_score", 0))
            results.extend(
                collect_all_ids(
                    best_comp, word_in_verse, component_index=i, depth=depth + 1
                )
            )

    return results


def _apply_apos_fallback(text: str, smm: SpeechMarkManager) -> str:
    """Apply apostrophes via speech_marks; take first variant for multi-variant words."""
    text = replace_speech_marks(text, smm)
    # replace_speech_marks joins multi-variant words with //; take first variant
    text = re.sub(r"([^/ \n\t]+)(?://[^/ \n\t]+)+", r"\1", text)
    return text
