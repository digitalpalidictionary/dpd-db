

from tools.paths import ProjectPaths
from pyglossary import Glossary


class ProgData():
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.wordnet_data: dict




def main():
    g = ProgData()

    input_file = g.pth.wordnet_data_path

    # Path to save the decompressed .dsl file
    output_file = '/home/bodhirasa/Documents/GoldenDict/selects/WordNet_3.0/En-En-WordNet3_gl_1_0.dsl'

    # Decompress the .dsl.dz file
    glossary = Glossary(g.pth.wordnet_data_path)

if __name__ == "__main__":
    main()