import re

from tools.cst_source.examples import find_gatha_example, find_sentence_example
from tools.cst_source.loader import make_cst_soup
from tools.cst_source.models import CstSourceSuttaExample
from tools.cst_source.parsers.base import BookParser
from tools.cst_source.parsers.registry import BOOK_PARSERS
from tools.cst_source.text_utils import clean_example
from tools.paths import ProjectPaths


def make_book_parser(book: str) -> BookParser | None:
    """Return a fresh parser instance for ``book``, or None if no parser
    handles it. Lets external callers drive the parsing engine manually."""
    parser_cls = BOOK_PARSERS.get(book)
    return parser_cls(book) if parser_cls is not None else None


def find_cst_source_sutta_example(
    book: str, text_to_find: str
) -> list[CstSourceSuttaExample]:
    pth = ProjectPaths()
    soups = make_cst_soup(pth, book)

    parser = make_book_parser(book)

    source_sutta_examples: list[CstSourceSuttaExample] = []

    for soup in soups:
        for x in soup.find_all(["head", "p"]):
            text = clean_example(x.text)

            # find examples
            example: list[str] = []
            if text_to_find is not None and re.findall(text_to_find, text):
                if "gatha" in x["rend"]:
                    example = find_gatha_example(x, text_to_find)
                else:
                    example = find_sentence_example(text, text_to_find)

            # find source and sutta
            if parser is None:
                continue
            parser.update(x)

            for ex in example:
                if (
                    parser.source
                    and parser.sutta
                    and CstSourceSuttaExample(parser.source, parser.sutta, ex)
                    not in source_sutta_examples
                ):
                    source_sutta_examples.append(
                        CstSourceSuttaExample(
                            source=parser.source,
                            sutta=parser.sutta,
                            example=ex,
                        )
                    )

    return source_sutta_examples
