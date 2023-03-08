from dataclasses import dataclass
from pathlib import Path


@dataclass()
class ResourcePaths():
    tipitaka_words_path: Path
    html_header_path: Path
    output_dir: Path
    output_html_dir: Path
    grammar_dict_pickle_path: Path
    goldedict_zip_path: Path
    mdict_output_path: Path


def get_paths() -> ResourcePaths:

    pth = ResourcePaths(
        tipitaka_words_path=Path(
            "frequency/output/word_count/tipitaka.csv"),
        html_header_path=Path(
            "grammar_dict/header.html"),
        output_dir=Path(
            "grammar_dict/output"),
        output_html_dir=Path(
            "grammar_dict/output/html"),
        grammar_dict_pickle_path=Path(
            "grammar_dict/output/grammar_dict_pickle"),
        goldedict_zip_path=Path(
            "exporter/share/dpd-grammar.zip"),
        mdict_output_path=Path(
            "exporter/share/dpd-grammar-mdict.mdx"),
    )

    # ensure dirs exist
    for d in [
        pth.output_dir,
        pth.output_html_dir
    ]:
        d.mkdir(parents=True, exist_ok=True)

    return pth
