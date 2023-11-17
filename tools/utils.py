from typing import List, TypedDict

class RenderResult(TypedDict):
    word: str
    definition_html: str
    definition_plain: str
    synonyms: List[str]

class RenderedSizes(TypedDict):
    dpd_header: int
    dpd_summary: int
    dpd_button_box: int
    dpd_grammar: int
    dpd_example: int
    dpd_inflection_table: int
    dpd_family_root: int
    dpd_family_word: int
    dpd_family_compound: int
    dpd_family_sets: int
    dpd_frequency: int
    dpd_feedback: int
    dpd_synonyms: int

    root_definition: int
    root_buttons: int
    root_info: int
    root_matrix: int
    root_families: int
    root_synonyms: int

    variant_readings: int
    variant_synonyms: int

    spelling_mistakes: int
    spelling_synonyms: int

    epd_header: int
    epd: int

    help: int

def default_rendered_sizes() -> RenderedSizes:
    return RenderedSizes(
        dpd_header = 0,
        dpd_summary = 0,
        dpd_button_box = 0,
        dpd_grammar = 0,
        dpd_example = 0,
        dpd_inflection_table = 0,
        dpd_family_root = 0,
        dpd_family_word = 0,
        dpd_family_compound = 0,
        dpd_family_sets = 0,
        dpd_frequency = 0,
        dpd_feedback = 0,
        dpd_synonyms = 0,

        root_definition = 0,
        root_buttons = 0,
        root_info = 0,
        root_matrix = 0,
        root_families = 0,
        root_synonyms = 0,

        variant_readings = 0,
        variant_synonyms = 0,

        spelling_mistakes = 0,
        spelling_synonyms = 0,

        epd_header = 0,
        epd = 0,

        help = 0,
    )

def sum_rendered_sizes(sizes: List[RenderedSizes]) -> RenderedSizes:
    res = default_rendered_sizes()
    for i in sizes:
        for k, v in i.items():
            res[k] += v
    return res

def list_into_batches(input_list: List, num_batches: int) -> List[List]:
    """Splits a list into a number of lists.

    When the division has remainder, this results in num + 1 batches, where the
    last batch has a small number of items, i.e. the remainder of the integer
    division.
    """

    batch_size = len(input_list) // num_batches

    if batch_size == 0:
        return [input_list]

    return [input_list[i:i + batch_size] for i in range(0, len(input_list), batch_size)]
