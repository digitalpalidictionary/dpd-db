"""The CC BY-NC-SA licence notice that rides along with DPD dictionary data.

Only the notice itself is tested here. Which routes attach it is checked by
reading the routes, not by running them: starting the web app loads the whole
dictionary into memory, and every search scans the 1.2 million row lookup table.
"""

from exporter.webapp.toolkit import (
    LICENSE_HTML,
    LICENSE_LINK_HEADER,
    LICENSE_NAME,
    LICENSE_NOTICE,
    LICENSE_URL,
)

CC_URL = "https://creativecommons.org/licenses/by-nc-sa/4.0/"


def test_link_header() -> None:
    assert LICENSE_LINK_HEADER == {
        "Link": f'<{CC_URL}>; rel="license"; title="CC BY-NC-SA 4.0"'
    }


def test_json_notice() -> None:
    assert set(LICENSE_NOTICE) == {"name", "url", "attribution", "note"}
    assert LICENSE_NOTICE["name"] == "CC BY-NC-SA 4.0"
    assert LICENSE_NOTICE["url"] == CC_URL
    # The machine-readable attribution still names the author; only the visible
    # notice under the entries dropped it.
    assert LICENSE_NOTICE["attribution"] == (
        "Digital Pāḷi Dictionary by Bodhirasa Bhikkhu CC BY-NC-SA 4.0"
    )
    assert LICENSE_NAME == "CC BY-NC-SA 4.0"
    assert LICENSE_URL == CC_URL


def test_visible_license_line() -> None:
    """Appended to the rendered entries, not to a page footer, so it travels with
    the data into GoldenDict, the JSON body and any third-party embed.
    """
    assert LICENSE_HTML.count('<div class="license-line">') == 1
    assert LICENSE_HTML.endswith("</div>")
    assert CC_URL in LICENSE_HTML
    assert "Digital Pāḷi Dictionary CC BY-NC-SA 4.0" in LICENSE_HTML
    assert "Bodhirasa" not in LICENSE_HTML


def test_cc_marks_are_inline() -> None:
    """Inlined, not linked, so the marks survive offline in GoldenDict — and
    `currentColor` so they read in both light and dark mode.
    """
    assert LICENSE_HTML.count("<svg") == 4
    assert 'fill="currentColor"' in LICENSE_HTML
    assert "<img" not in LICENSE_HTML
