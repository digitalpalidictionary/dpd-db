"""Client for the Dharmamitra public translation API.

Used to fetch an unreviewed, contextual gloss of a specific word as used in
a specific Pali sentence. The endpoint is public and requires no API key.
"""

import requests

_TRANSLATE_URL = "https://dharmamitra.org/api-search/cat-translate/v1/translate"
_TIMEOUT_SECONDS = 30


def get_contextual_gloss(example_sentence: str, lemma: str) -> str | None:
    """Ask Dharmamitra to translate `example_sentence` and gloss `lemma` in context.

    Returns the translation response text, or None if the request fails for
    any reason (network error, non-200 status, malformed response).
    """
    style_instruction = (
        "After translating, add one line: WORD GLOSS: explain specifically "
        f'what the word "{lemma}" means as used in this exact sentence, '
        "in this exact grammatical form."
    )
    payload = {
        "input_pali": example_sentence,
        "focus": "pali",
        "target_language": "english",
        "style_instruction": style_instruction,
    }

    try:
        response = requests.post(_TRANSLATE_URL, json=payload, timeout=_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        return data["translation"]
    except (requests.RequestException, ValueError, KeyError):
        return None
