"""Tests for tools/utils.py helpers."""

import pytest

from tools.utils import default_rendered_sizes, extract_body, sum_rendered_sizes


def test_extract_body_splits_header_from_body() -> None:
    html = "<head><style>.dpd {}</style></head>\n<body>\n<div class='dpd'>x</div>"
    assert extract_body(html) == "<body>\n<div class='dpd'>x</div>"


def test_extract_body_at_start_of_string() -> None:
    html = "<body><p>y</p>"
    assert extract_body(html) == html


def test_extract_body_missing_tag_raises() -> None:
    with pytest.raises(ValueError, match="no <body> tag"):
        extract_body("<head></head><p>no body here</p>")


def test_extract_body_attribute_on_body_tag_raises() -> None:
    with pytest.raises(ValueError, match="no <body> tag"):
        extract_body("<head></head><body class='dpd'><p>z</p>")


def test_sum_rendered_sizes_of_nothing_is_all_zeros() -> None:
    assert sum_rendered_sizes([]) == default_rendered_sizes()


def test_sum_rendered_sizes_adds_every_key() -> None:
    a = default_rendered_sizes()
    a["dpd_header"] = 3
    a["epd"] = 7
    b = default_rendered_sizes()
    b["dpd_header"] = 4
    b["root_info"] = 5

    total = sum_rendered_sizes([a, b])

    assert total["dpd_header"] == 7
    assert total["epd"] == 7
    assert total["root_info"] == 5
    assert total["dpd_summary"] == 0


def test_sum_rendered_sizes_keeps_the_full_key_set() -> None:
    """Summing must not drop or invent keys — the exporters index every field."""
    total = sum_rendered_sizes([default_rendered_sizes(), default_rendered_sizes()])
    assert total.keys() == default_rendered_sizes().keys()


def test_sum_rendered_sizes_does_not_mutate_its_inputs() -> None:
    a = default_rendered_sizes()
    a["dpd_header"] = 2
    b = default_rendered_sizes()
    b["dpd_header"] = 6

    sum_rendered_sizes([a, b])

    assert a["dpd_header"] == 2
    assert b["dpd_header"] == 6
