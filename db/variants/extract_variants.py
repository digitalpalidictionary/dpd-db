"""Extract variants readings from all Pāḷi texts."""

from db.variants.extract_variants_from_sc import extract_variants_from_sc
from db.variants.variant_types import VariantsDict

from db.variants.extract_variants_from_cst import extract_variants_from_cst
from db.variants.variants_exporter import save_json, export_to_goldendict_mdict

from tools.paths import ProjectPaths
from tools.printer import p_title
from tools.tic_toc import tic, toc

pth: ProjectPaths = ProjectPaths()


def main():

    tic()
    p_title("variants dict")
    
    variants_dict: VariantsDict = {}  

    variants_dict = extract_variants_from_cst(variants_dict, pth)
    variants_dict = extract_variants_from_sc(variants_dict, pth)

    save_json(variants_dict)
    export_to_goldendict_mdict(variants_dict)

    toc()

if __name__ == "__main__":
    main()


# TODO get correct book names
# TODO sort entries by book order
# TODO add synonyms
# TODO makes a p_green_line with two variables
# TODO synonyms with ṃ and ṁ
# TODO synonyms with punctuation and no punctuation
