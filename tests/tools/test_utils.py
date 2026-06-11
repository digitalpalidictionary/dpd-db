"""Tests for tools/utils.py helpers."""

import pytest

from tools.utils import extract_body


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
