"""Split hidden detail panels out of DPD results HTML.

A heavy entry such as "dhamma" sends about 2.3 MB of HTML, most of it inside
hidden panels (grammar, families, declensions, frequency) that the reader may
never open. Sending their contents separately lets the browser build each one
only when it is opened, instead of building every panel for every search.
"""

import re

_DIV_TAG = re.compile(r"<div\b[^>]*>|</div\s*>", re.IGNORECASE)
_ID = re.compile(r'\bid="([^"]+)"')
_CLASS = re.compile(r'\bclass="([^"]*)"')


def split_hidden_panels(html: str) -> tuple[str, dict[str, str]]:
    """Return the HTML with each outermost hidden panel emptied, and the
    removed contents keyed by panel id.

    A panel is a div with an id and the class "hidden". Panels nested inside
    another hidden panel stay in their parent's contents. A panel ends at the
    </div> that closes it by depth, as the browser's parser ends it, so stray
    tags elsewhere (results have one stray </div> per headword) still split.
    If a panel is never closed or an id repeats, the HTML is returned whole,
    with no panels, so the page still shows everything."""

    depth = 0
    open_panel: tuple[int, str, int] | None = None
    ranges: list[tuple[str, int, int]] = []

    for tag in _DIV_TAG.finditer(html):
        if tag.group(0)[1] == "/":
            if open_panel and open_panel[0] == depth:
                panel_id, start = open_panel[1], open_panel[2]
                ranges.append((panel_id, start, tag.start()))
                open_panel = None
            depth -= 1
        else:
            depth += 1
            if open_panel is None:
                classes = _CLASS.search(tag.group(0))
                panel_id = _ID.search(tag.group(0))
                if classes and panel_id and "hidden" in classes.group(1).split():
                    open_panel = (depth, panel_id.group(1), tag.end())

    ids = [panel_id for panel_id, _, _ in ranges]
    if open_panel is not None or len(set(ids)) != len(ids):
        return html, {}

    panels = {panel_id: html[start:end] for panel_id, start, end in ranges}
    parts = []
    position = 0
    for _, start, end in ranges:
        parts.append(html[position:start])
        position = end
    parts.append(html[position:])
    return "".join(parts), panels
