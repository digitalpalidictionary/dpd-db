CONE_PROMPT = """Extract information for the Pali word {word} from this dictionary HTML.

HTML:
{html}

Look for {word} in the HTML. It might be:
1. The main headword at the top (note: may have parentheses like {word_parentheses} or be abbreviated with a hyphen like "°-ma(t)")
2. A sub-entry marked with class="subsense H3 highlight" (note: may have parentheses like {word_parentheses} or be abbreviated with a hyphen like "°-ma(t)")

Extract:
1. The part of speech (e.g., mfn., m., n., f., ind., pr. 3 sg., aor. 3 sg., etc.)
2. The English meaning/definition

IMPORTANT: Use SEMICOLONS (;) to separate multiple meanings. NEVER use commas.

Return ONLY in this exact format:
POS | MEANING

Your response:"""

CPD_PROMPT = """Extract information for the Pali word {word} from this dictionary HTML.

HTML:
{html}

Look for {word} in the HTML and extract:
1. The part of speech (e.g., mfn., m., n., f., ind., etc.)
2. The English meaning/definition (semicolon-separated if multiple meanings)

Note: the word may appear with parentheses like {word_parentheses} or be abbreviated with a hyphen.

Return ONLY in this exact format:
POS | MEANING

Your response:"""
