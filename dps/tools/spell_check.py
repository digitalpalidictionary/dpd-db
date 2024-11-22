"""Functions related spellcheck."""

import textwrap

from rich import print

from spellchecker import SpellChecker

from tools.tokenizer import split_words


class SpellCheck:
    def __init__(self, serialized_dict_path):
        self.ru_spell = SpellChecker(language='ru')
        self.load_custom_dictionary(serialized_dict_path)

    def load_custom_dictionary(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            custom_words = set(f.read().splitlines())
        self.custom_words = custom_words
        self.ru_spell.word_frequency.load_words(custom_words)

    def check_spelling(self, field_value):
        ru_sentence = field_value
        ru_words = split_words(ru_sentence)
        ru_misspelled = self.ru_spell.unknown(ru_words)

        if ru_misspelled:
            print(f"offline ru_misspelled {ru_misspelled}")

        # Check custom dictionary only for misspelled words
        truly_misspelled = [word for word in ru_misspelled if word not in self.custom_words]

        if truly_misspelled:
            # For the truly misspelled words, obtain suggestions from the local spellchecker
            suggestions = []
            for word in truly_misspelled:
                candidates = self.ru_spell.candidates(word)
                if candidates:  # Ensure candidates is not None
                    suggestions.extend(candidates)

            # If no suggestions were found, display a custom message
            if not suggestions:
                return "?"

            # Else process and display the suggestions
            # Joining the flattened list
            correction_text = ", ".join(suggestions)

            # Wrap the correction_text and join it into a multiline string
            wrapped_correction = "\n".join(textwrap.wrap(correction_text, width=30))  # Assuming width of 30 characters
            return wrapped_correction

        else:
            return ""
