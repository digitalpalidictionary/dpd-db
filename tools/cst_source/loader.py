from bs4 import BeautifulSoup

from tools.pali_text_files import cst_texts
from tools.paths import ProjectPaths


def get_cst_filenames(books: list[str] | str) -> list[str]:
    """Take a single book OR a list of books
    and return the relevant filenames."""

    filenames: list[str] = []

    if type(books) is list:
        for book in books:
            if book in cst_texts:
                filenames.extend(cst_texts[book])

    elif type(books) is str and books in cst_texts:
        filenames.extend(cst_texts[books])

    return filenames


def make_cst_soup(
    pth: ProjectPaths,
    books: list[str] | str,
    unwrap_notes: bool = True,
) -> list[BeautifulSoup]:
    """Take a book (or list of books) and return a list of soups."""

    soups: list[BeautifulSoup] = []

    for filename in get_cst_filenames(books):
        filename = filename.replace(".txt", ".xml")

        with open(pth.cst_xml_dir.joinpath(filename), "r", encoding="UTF-16") as f:
            xml = f.read()

        soup = BeautifulSoup(xml, "xml")

        # remove all the "pb" tags
        pbs = soup.find_all("pb")
        for pb in pbs:
            pb.decompose()

        if unwrap_notes:
            # unwrap all the notes (variant readings)
            notes = soup.find_all("note")
            for note in notes:
                note.replace_with(rf" [{note.text}] ")

        # unwrap all the hi parunum dot tags (paragraphy numbers)
        his = soup.find_all("hi", rend=["paranum", "dot"])
        for hi in his:
            hi.unwrap()

        soups.append(soup)

    return soups
