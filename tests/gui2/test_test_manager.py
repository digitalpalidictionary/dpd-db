"""Opening the tests TSV from an add view works before any test has run."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from gui2.pass1_add_view import Pass1AddView
from gui2.pass2_add_view import Pass2AddView
from gui2.test_manager import GuiTestManager


def test_open_test_file_before_any_test_run_reports_to_the_view(
    tmp_path: Path,
) -> None:
    # A fresh manager, as at the start of a session: run_all_tests has never
    # set its ui or page.
    manager = GuiTestManager.__new__(GuiTestManager)
    missing = tmp_path / "missing.tsv"
    manager.toolkit = SimpleNamespace(  # pyright: ignore[reportAttributeAccessIssue]
        project_paths=SimpleNamespace(internal_tests_path=missing)
    )
    view = MagicMock()

    manager.open_test_file(view)

    view.update_message.assert_called_once_with(
        f"Error: Test file not found at expected path: {missing}"
    )


@pytest.mark.parametrize("view_class", [Pass1AddView, Pass2AddView])
def test_test_button_with_empty_lemma_opens_the_file_for_this_view(
    view_class: type,
) -> None:
    view = MagicMock(spec=view_class)
    # Set in __init__, so the class spec does not know them.
    view.dpd_fields = MagicMock()
    view.dpd_fields.get_field.return_value = SimpleNamespace(value="")
    view.test_manager = MagicMock()
    view.page = MagicMock()
    view.add_to_db_button = MagicMock()
    view._add_to_db_button = MagicMock()

    view_class._click_run_tests(view, None)

    view.test_manager.open_test_file.assert_called_once_with(view)
