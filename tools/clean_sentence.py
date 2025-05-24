import re
from tools.pali_alphabet import pali_alphabet


def split_pali_sentence_into_words(
    text: str,
    include_apostrophe=True,
    include_hyphen=True,
) -> list[str]:
    """
    Split a Pāḷi sentence into a list of words.

    Optionally include `'` and `-`.
    """

    text = text.replace("<b>", "").replace("</b>", "")

    if not text:
        return []

    if include_apostrophe:
        pali_alphabet.append("'")
    else:
        text.replace("'", "")

    if include_hyphen:
        pali_alphabet.append("-")
    else:
        text.replace("-", "")

    pali_alphabet_string = "".join(pali_alphabet)
    word_finder_pattern = f"[{pali_alphabet_string}]+"
    words = re.findall(word_finder_pattern, text)

    return words


if __name__ == "__main__":
    # Example usage:
    sentence = (
        "(DNa) soceyyasīlālayuposathesu cā'ti ettha kāyasoceyy'ādi tividhaṃ soceyyaṃ."
    )

    words_list = split_pali_sentence_into_words(sentence)
    print(words_list)

    # Another example
    sentence2 = "eka-puggalaṃ āgamma, na tveva dhammaṃ."
    words_list2 = split_pali_sentence_into_words(sentence2, include_hyphen=False)
    print(words_list2)
