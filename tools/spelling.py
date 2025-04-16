from spellchecker import SpellChecker
from tools.paths import ProjectPaths
from typing import Dict, List


class CustomSpellChecker:
    def __init__(self) -> None:
        """Initialize the spell checker with custom dictionary."""

        self.spell = SpellChecker(language="en")
        self.pth = ProjectPaths()
        self.user_dict = self.pth.user_dict_path

        # Load custom dictionary
        with open(self.user_dict, "r") as f:
            custom_words = [line.strip() for line in f if line.strip()]
            self.spell.word_frequency.load_words(custom_words)

    def check_sentence(self, sentence: str) -> Dict[str, List[str]]:
        """Check spelling in a sentence and return misspelled words with suggestions."""

        # Split the sentence into words and remove punctuation
        words = "".join(
            c if c.isalpha() or c.isspace() else " " for c in sentence
        ).split()

        # Find misspelled words
        misspelled = self.spell.unknown(words)

        # Get suggestions for each misspelled word
        results: Dict[str, List[str]] = {}
        for word in misspelled:
            candidates = self.spell.candidates(word)
            results[word] = list(candidates) if candidates else []

        return results

    def add_to_dictionary(self, word: str) -> str:
        """Add a word to both the session dictionary and the custom dictionary file."""
        # Add to the current spell checker session
        self.spell.word_frequency.load_words([word])

        # Add to the custom dictionary file if provided
        if self.user_dict:
            with open(self.user_dict, "a") as f:
                f.write(f"{word}\n")

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
