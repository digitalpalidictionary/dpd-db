"""Type definitions for the Pali analysis pipeline."""

from typing import TypedDict


class AnalysisOption(TypedDict, total=False):
    key: str
    id: int | str
    lemma: str
    degree_of_completion: str
    score: int
    pali: str
    pos: str
    grammar: str
    meaning_1: str
    meaning_combo: str
    compound_type: str
    compound_construction: str
    root_key: str
    construction: str
    example_1: str
    source_1: str
    example_2: str
    source_2: str
    components: list[list["AnalysisOption"]]


class AnalysisResult(TypedDict):
    word: str
    status: str
    data: list[AnalysisOption]
