from json import load

from tools.paths import ProjectPaths
from tools.printer import printer as pr
from rich import print


class HyphenationFileManager:
    """
    ## usage
    `hm = HyphenationFileManager()` \\
    `hyphenation_dict = hm.load_hyphenations_dict()`
    ## return type
    `dict[str, str]`
    """

    def __init__(self):
        self.pth: ProjectPaths = ProjectPaths()
        self.load_hyphenations_dict()

    def load_hyphenations_dict(self):
        if self.pth.add_hyphenations_dict.exists():
            with open(self.pth.add_hyphenations_dict) as file:
                hyphenations_dict = load(file)
                return hyphenations_dict["exceptions"]
        else:
            pr.red("no hyphenations dict found")
            return {}


if __name__ == "__main__":
    # usage
    hm = HyphenationFileManager()
    hyphenation_dict = hm.load_hyphenations_dict()
    print(hyphenation_dict)
