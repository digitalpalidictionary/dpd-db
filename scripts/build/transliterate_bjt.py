"""Transliterate tipitaka.lk BJT texts from Sinhala to Roman script and
save as JSON, text, and complete books. Prerequisite prep step for the
scripts/suttas/bjt/ pipeline, which reads bjt_roman_json_dir directly.
Run manually when the BJT submodule updates."""

import json

from tools.bjt import get_bjt_file_names, get_bjt_json, process_single_bjt_file
from tools.pali_text_files import bjt_texts
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.sinhala_tools import translit_si_to_ro


def transliterate_json(pth: ProjectPaths) -> None:
    """Transliterate every Sinhala BJT JSON file to Roman script."""
    pr.tic()
    pr.yellow_title("transliterating tipitaka.lk json files")

    files = [f.name for f in pth.bjt_sinhala_dir.iterdir() if f.name != ".DS_Store"]
    for counter, file in enumerate(files, 1):
        pr.counter(counter, len(files), file)
        in_path = pth.bjt_sinhala_dir / file
        out_path = pth.bjt_roman_json_dir / file

        sinhala = in_path.read_text(encoding="utf-8")
        roman = translit_si_to_ro(sinhala)
        out_path.write_text(roman, encoding="utf-8")

    pr.toc()


def get_file_names(pth: ProjectPaths) -> list[str]:
    pr.green_tmr("get actual file names")
    file_names = sorted(
        f.name for f in pth.bjt_sinhala_dir.iterdir() if f.name != ".DS_Store"
    )
    pr.yes(len(file_names))
    return file_names


def test_file_names(pth: ProjectPaths) -> None:
    """Diagnostic: compare filenames on disk against bjt_texts' expected list."""
    pr.yellow_title("test file names")

    file_names = get_file_names(pth)

    pr.green_tmr("get dict file names")
    bjt_files = [file_name for book in bjt_texts for file_name in bjt_texts[book]]
    pr.yes(len(bjt_files))

    pr.green_tmr("difference 1")
    pr.yes(str(set(bjt_files).symmetric_difference(set(file_names))))
    pr.green_tmr("difference 2")
    pr.yes(str(set(file_names).symmetric_difference(set(bjt_files))))


def make_index(pth: ProjectPaths) -> None:
    """Make an index of {collection: {"book_id": 12, "filenames": [...]}}."""
    pr.yellow_title("making index")
    file_names = get_file_names(pth)
    json_dicts = get_bjt_json(file_names)
    index_dict: dict[str, dict] = {"mula": {}, "atta": {}}

    for jd in json_dicts:
        file_name = jd["filename"]
        book_id = jd["bookId"]
        collection = jd.get("collection", "mula")
        index_dict[collection].setdefault(book_id, []).append(file_name)

    list_of_tuples = [
        (collection, book_id, filenames)
        for collection, data in index_dict.items()
        for book_id, filenames in data.items()
    ]
    list_of_tuples.sort(key=lambda x: x[2])
    list_of_tuples.sort(key=lambda x: x[1])
    list_of_tuples.sort(key=lambda x: x[0], reverse=True)

    save_path = pth.bjt_dir / "index.json"
    save_path.write_text(
        json.dumps(list_of_tuples, ensure_ascii=False, indent=1), encoding="utf-8"
    )


def save_books(pth: ProjectPaths) -> None:
    """Save each book in BJT to a text file."""
    pr.tic()
    pr.yellow_title("saving BJT books")

    for counter, book in enumerate(bjt_texts):
        pr.counter(counter, len(bjt_texts), book)
        bjt_file_names = get_bjt_file_names([book])
        json_dicts = get_bjt_json(bjt_file_names)
        bjt_text = "".join(
            process_single_bjt_file(
                json_dict,
                convert_bold_tags=False,
                footnotes_inline=False,
                show_page_numbers=True,
                show_metadata=True,
            )
            for json_dict in json_dicts
        )

        file_path = (pth.bjt_books_dir / book).with_suffix(".txt")
        file_path.write_text(bjt_text, encoding="utf-8")
    pr.toc()


def save_text_files(pth: ProjectPaths) -> None:
    """Save all BJT json to text files."""
    pr.tic()
    pr.yellow_title("saving BJT to text files")

    files = [f.name for f in pth.bjt_roman_json_dir.iterdir() if f.name != ".DS_Store"]
    for counter, file in enumerate(files, 1):
        pr.counter(counter, len(files), file)
        bjt_dicts = get_bjt_json([file])
        bjt_text = "".join(process_single_bjt_file(bjt_dict) for bjt_dict in bjt_dicts)
        file_path = pth.bjt_roman_txt_dir / f"{file}.txt"
        file_path.write_text(bjt_text, encoding="utf-8")
    pr.toc()


def main() -> None:
    pth = ProjectPaths()
    transliterate_json(pth)
    save_books(pth)
    save_text_files(pth)


if __name__ == "__main__":
    main()
