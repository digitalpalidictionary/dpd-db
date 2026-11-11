"""Time gui2 view imports: `start` = the desktop's first tab only, `all` =
every view module gui2/main.py imports before first paint.

Phase 4 moved Pass1AddView's import out of App.__init__ into _make_pass1_add,
so the __init__ group is 10 modules today, not the plan's original 11; the
module-top group is the plan's 5. Lists copied from gui2/main.py, not memory.
"""

import sys
import time

import flet  # noqa: F401  (untimed, as gui2.main does at module top)
import gui2.toolkit  # noqa: F401

START_MODULES = [
    "gui2.global_tab_view",
]

ALL_MODULES = [
    # module top (gui2/main.py imports before the window paints)
    "gui2.compound_type_tab_view",
    "gui2.roots_tab_view",
    "gui2.sandhi_find_replace_view",
    "gui2.sandhi_view",
    "gui2.spelling_find_replace_view",
    # App.__init__ (before first paint)
    "gui2.global_tab_view",
    "gui2.inflection_templates_tab_view",
    "gui2.pass1_auto_view",
    "gui2.pass2_add_view",
    "gui2.pass2_auto_view",
    "gui2.pass2_pre_view",
    "gui2.pass2x.in_commentary_view",
    "gui2.bold_search_view",
    "gui2.tests_tab_view",
    "gui2.translations_view",
]


def main() -> None:
    variant = sys.argv[1]
    modules = START_MODULES if variant == "start" else ALL_MODULES
    t0 = time.perf_counter()
    for name in modules:
        __import__(name)
    print(f"{variant} {time.perf_counter() - t0:.3f}")


if __name__ == "__main__":
    main()
