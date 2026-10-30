"""A read tab refuses every action that writes, and touches nothing."""

from unittest.mock import MagicMock

import pytest

from gui2.contributor_tabs import READ_ONLY_MESSAGE
from gui2.filter_component import FilterComponent
from gui2.filter_tab_view import FilterTabView
from gui2.inflection_templates_tab_view import InflectionTemplatesTabView
from gui2.roots_tab_view import RootsTabView


def _snackbar(monkeypatch: pytest.MonkeyPatch, module: str) -> MagicMock:
    """Replace the module's snackbar and the unmounted-page lookup."""
    snackbar = MagicMock()
    monkeypatch.setattr(f"{module}.show_global_snackbar", snackbar)
    return snackbar


def _stub_page(monkeypatch: pytest.MonkeyPatch, *classes: type) -> None:
    # Flet 1.0 raises on `.page` of an unmounted control.
    for cls in classes:
        monkeypatch.setattr(cls, "page", MagicMock(), raising=False)


def _refused(snackbar: MagicMock) -> bool:
    return any(READ_ONLY_MESSAGE in call.args for call in snackbar.call_args_list)


@pytest.mark.parametrize("handler", ["_save_root", "_delete_root"])
@pytest.mark.parametrize("read_only", [True, False])
def test_roots_write_handlers(
    monkeypatch: pytest.MonkeyPatch, handler: str, read_only: bool
) -> None:
    snackbar = _snackbar(monkeypatch, "gui2.roots_tab_view")
    _stub_page(monkeypatch, RootsTabView)
    toolkit = MagicMock()
    view = RootsTabView(MagicMock(), toolkit)
    view.read_only = read_only
    toolkit.db_manager.reset_mock()

    getattr(view, handler)(None)

    assert _refused(snackbar) is read_only
    if read_only:
        assert toolkit.db_manager.method_calls == []
        assert snackbar.call_count == 1


@pytest.mark.parametrize(
    "handler", ["_save_template", "_rename_template", "_delete_template"]
)
@pytest.mark.parametrize("read_only", [True, False])
def test_template_write_handlers(
    monkeypatch: pytest.MonkeyPatch, handler: str, read_only: bool
) -> None:
    toolkit = MagicMock()
    view = InflectionTemplatesTabView(MagicMock(), toolkit)
    view.read_only = read_only
    toolkit.db_manager.reset_mock()

    getattr(view, handler)(None)

    if read_only:
        assert view._message_field.value == READ_ONLY_MESSAGE
        assert toolkit.db_manager.method_calls == []
    else:
        assert view._message_field.value != READ_ONLY_MESSAGE


def _filter_view(read_only: bool) -> tuple[FilterTabView, MagicMock]:
    toolkit = MagicMock()
    view = FilterTabView(MagicMock(), toolkit)
    view.read_only = read_only
    component = MagicMock(spec=FilterComponent)
    view.filter_component_container.content = component
    return view, component


@pytest.mark.parametrize("read_only", [True, False])
def test_filter_tab_save_changes(
    monkeypatch: pytest.MonkeyPatch, read_only: bool
) -> None:
    snackbar = _snackbar(monkeypatch, "gui2.filter_tab_view")
    _stub_page(monkeypatch, FilterTabView)
    view, component = _filter_view(read_only)
    monkeypatch.setattr(
        "gui2.filter_tab_view.FilterComponent", type(component), raising=False
    )

    view._save_changes_clicked(None)  # pyright: ignore[reportArgumentType]

    assert _refused(snackbar) is read_only
    assert component._save_changes.called is (not read_only)


def test_filter_component_save_button_refuses_when_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The on-screen Save Changes button calls the component, not the tab view.
    snackbar = _snackbar(monkeypatch, "gui2.filter_component")
    _stub_page(monkeypatch, FilterComponent)
    toolkit = MagicMock()
    component = FilterComponent(MagicMock(), toolkit, read_only=True)
    component.modified_cells = {(1, "meaning_1"): "changed"}
    toolkit.db_manager.reset_mock()

    component._save_changes(None)

    assert _refused(snackbar)
    assert toolkit.db_manager.method_calls == []
    assert component.modified_cells == {(1, "meaning_1"): "changed"}


def test_filter_tab_hands_read_only_to_its_components(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[dict[str, object]] = []

    def fake_component(**kwargs: object) -> MagicMock:
        created.append(kwargs)
        return MagicMock()

    _stub_page(monkeypatch, FilterTabView)
    view = FilterTabView(MagicMock(), MagicMock())
    view.read_only = True
    monkeypatch.setattr("gui2.filter_tab_view.FilterComponent", fake_component)

    view._apply_filters_clicked(None)  # pyright: ignore[reportArgumentType,reportAttributeAccessIssue]

    assert created and created[0]["read_only"] is True
