# -*- coding: utf-8 -*-
"""Thread-safe singleton English spell checker with a user-defined custom
dictionary. Used by gui2 to check spelling in meaning fields."""

import re
import threading
from spellchecker import SpellChecker
from tools.paths import ProjectPaths

# Letters with an internal apostrophe (e.g. "didn't", "isn't") stay one word;
# any other punctuation is treated as a word boundary.
_WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)*")


class CustomSpellChecker:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls) -> "CustomSpellChecker":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the spell checker with custom dictionary (only once)."""
        if CustomSpellChecker._initialized:
            return

        with CustomSpellChecker._lock:
            if CustomSpellChecker._initialized:
                return

            self.spell = SpellChecker(language="en")
            self.pth = ProjectPaths()
            self.user_dict = self.pth.user_dict_path

            # Load custom dictionary
            with open(self.user_dict, "r", encoding="utf-8") as f:
                custom_words = [line.strip() for line in f if line.strip()]
                self.spell.word_frequency.load_words(custom_words)

            CustomSpellChecker._initialized = True

    def check_sentence(self, sentence: str) -> dict[str, list[str]]:
        """Check spelling in a sentence and return misspelled words with suggestions."""

        # Use lock to prevent concurrent access to the shared SpellChecker instance
        with CustomSpellChecker._lock:
            words = _WORD_RE.findall(sentence)

            # Find misspelled words
            misspelled = self.spell.unknown(words)

            # Get suggestions for each misspelled word
            results: dict[str, list[str]] = {}
            for word in misspelled:
                candidates = self.spell.candidates(word)
                results[word] = list(candidates) if candidates else []

            return results

    def has_misspellings(self, sentence: str) -> bool:
        """Fast boolean spell check: no suggestion generation, which is what
        makes check_sentence expensive (candidates() explores all edit-
        distance variants per unknown word). Use this when only a yes/no
        answer is needed, e.g. to color a cell."""
        with CustomSpellChecker._lock:
            words = _WORD_RE.findall(sentence)
            return bool(self.spell.unknown(words))

    def add_to_dictionary(self, word: str) -> str:
        """Add a word to the session dictionary and rewrite the custom dictionary file sorted and deduplicated."""
        with CustomSpellChecker._lock:
            self.spell.word_frequency.load_words([word])
            if self.user_dict:
                with open(self.user_dict, "r", encoding="utf-8") as f:
                    words = {line.strip() for line in f if line.strip()}
                words.add(word.strip())
                with open(self.user_dict, "w", encoding="utf-8") as f:
                    f.write(
                        "\n".join(sorted(words, key=lambda w: (w.lower(), w))) + "\n"
                    )

        return f"Added '{word}' to dictionary"


# Example usage
if __name__ == "__main__":
    # Initialize with a custom dictionary file
    checker = CustomSpellChecker()

    # Example sentence with mistakes
    test_sentence = "This is a testt sentense with som speling mistakes."

    # Check spelling and get suggestions
    misspelled_words = checker.check_sentence(test_sentence)

    # Print results
    if misspelled_words:
        print("Misspelled words and suggestions:")
        for word, suggestions in misspelled_words.items():
            print(f"- {word}: {', '.join(suggestions)}")
    else:
        print("No spelling mistakes found.")

    # Add a custom word to the dictionary
    print(checker.add_to_dictionary("sentense"))

    # Check the sentence again
    misspelled_words = checker.check_sentence(test_sentence)
    print("\nAfter adding 'sentense' to dictionary:")
    if misspelled_words:
        print("Misspelled words and suggestions:")
        for word, suggestions in misspelled_words.items():
            print(f"- {word}: {', '.join(suggestions)}")
    else:
        print("No spelling mistakes found.")
