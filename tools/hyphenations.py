from json import dump, load

from tools.paths import ProjectPaths
from tools.printer import printer as pr
from rich import print

HyphenationsDict = dict[str, str]


class HyphenationFileManager:
    """
    ### usage
    `hm = HyphenationFileManager()` \\
    `hyphenation_dict = hm.load_hyphenations_dict()`
    ### return type
    `HyphenationsDict`
    """

    def __init__(self):
        self.pth: ProjectPaths = ProjectPaths()
        self.hyphenations_dict: HyphenationsDict
        self.load_hyphenations_dict()

    def load_hyphenations_dict(self):
        if self.pth.hyphenations_dict_path.exists():
            with open(self.pth.hyphenations_dict_path) as file:
                self.hyphenations_dict = load(file)
                return self.hyphenations_dict
        else:
            pr.red("no hyphenations dict found")
            return {}

    def save_hyphenations_dict(self):
        with open(self.pth.hyphenations_dict_path, "w") as file:
            dump(self.hyphenations_dict, file, ensure_ascii=False, indent=2)

    def update_hyphenations_dict(self, hyphenated_word):
        pure_word = hyphenated_word.replace("'", "").replace("-", "")
        if pure_word and pure_word not in self.hyphenations_dict:
            self.hyphenations_dict[pure_word] = hyphenated_word
            self.save_hyphenations_dict()
            print(f"updated hyphenations with {pure_word}: {hyphenated_word}")
        elif pure_word and pure_word in self.hyphenations_dict:
            pr.error(f"{hyphenated_word} already exists.")
        else:
            pr.error(f"empty word: {pure_word}")


if __name__ == "__main__":
    # usage
    hm = HyphenationFileManager()
    # hyphenation_dict = hm.load_hyphenations_dict()
    # print(hyphenation_dict)
    hm.update_hyphenations_dict("test-a-testy")
