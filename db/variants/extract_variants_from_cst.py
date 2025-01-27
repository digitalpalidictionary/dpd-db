"""Extract variants readings from CST texts."""

from pathlib import Path
from bs4 import BeautifulSoup

from db.variants.variant_types import VariantsDict

from tools.pali_alphabet import pali_alphabet
from tools.pali_text_files import cst_texts
from tools.paths import ProjectPaths
from tools.printer import p_counter, p_green_title
from tools.tic_toc import bip


def get_cst_file_list(pth: ProjectPaths) -> list[Path]:
    """Get a list of CST files."""

    cst_xml_dir: Path = pth.cst_xml_dir
    files: list[Path] = [f for f in cst_xml_dir.iterdir() if f.is_file()]
    return files


def make_soup(file: Path) -> BeautifulSoup:
    """Make a soup from a CST file."""

    with open(file, "r", encoding="UTF-16") as f:
        file_contents: str = f.read()
        soup: BeautifulSoup = BeautifulSoup(file_contents, "xml")

        # remove all the "pb" tags
        pbs = soup.find_all("pb")
        for pb in pbs:
            pb.decompose()
        
        # remove all the hi parunum dot tags
        his = soup.find_all("hi", rend=["paranum", "dot"])
        for hi in his:
            hi.unwrap()

        return soup


def key_cleaner(key: str) -> str:
    """Remove non-Pāḷi characters from the key"""
    
    key_clean: str = ''.join(c for c in key.lower() if c in pali_alphabet)
    key_clean = key_clean.lower()
    return key_clean


def extract_variants(
    soup: BeautifulSoup,
    variants_dict: VariantsDict,
    book_name: str
) -> VariantsDict:
    """Extract variants from a CST file."""

    notes = soup.find_all('note')
    for note in notes:
        # Get preceding text node
        preceding_text = note.previous_sibling

        if preceding_text and not preceding_text.text.strip():
            preceding_text = note.previous_sibling.previous_sibling
        
        if preceding_text:
            text_str: str = preceding_text.text.strip()
            if text_str:
                # Split text into words and get last word before note
                words: list[str] = text_str.split()
                if words:
                    key: str = words[-1]
                    key_clean: str = key_cleaner(key)
                    value: str = note.get_text(strip=True).lower()                 

                    # ensure outer dictionary entry exists
                    if key_clean not in variants_dict:
                        variants_dict[key_clean] = {}
                    
                    # ensure cst entry exists
                    if "cst" not in variants_dict[key_clean]:
                        variants_dict[key_clean]['cst'] = {}

                    # ensure inner dictionary entry exists
                    if book_name not in variants_dict[key_clean]["cst"]:
                        variants_dict[key_clean]["cst"][book_name] = []

                    variants_dict[key_clean]["cst"][book_name].append(value)

    return variants_dict


def get_book_name(xml_filename: Path) -> str:
    """Convert filename.xml into a book code."""

    txt_filename: str = str(xml_filename.with_suffix(".txt").name)
    
    # Search through the dictionary
    for key, txt_files in cst_texts.items():
        if any(file == txt_filename for file in txt_files):
            return key
    raise ValueError(f"No matching key found for XML file: {xml_filename}")


def process_cst(
        variants_dict: VariantsDict,
        pth: ProjectPaths
) -> VariantsDict:
    
    p_green_title("extracting variants from CST texts")
    files: list[Path] = get_cst_file_list(pth)

    bip()
    for counter, file_name in enumerate(files):

        if counter % 25 == 0:
            p_counter(counter, len(files), file_name.name)
            bip()

        # debugging only
        # if file_name.name != "s0301m.mul.xml":
        #     continue

        soup: BeautifulSoup = make_soup(file_name)
        book_name: str = get_book_name(file_name)
        variants_dict = extract_variants(soup, variants_dict, book_name)

    return variants_dict
    