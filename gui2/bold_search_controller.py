from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gui2.bold_search_view import BoldSearchView
    from gui2.toolkit import ToolKit


class BoldSearchController:
    def __init__(
        self,
        view: "BoldSearchView",
        toolkit: "ToolKit",
    ) -> None:
        self.view = view
        self.toolkit = toolkit

    def perform_search(self, e):
        search_bold = self.view.search_bold_field.value
        search_within = self.view.search_within_field.value

        if not search_bold and not search_within:
            self.view.update_results([], "")
            return

        # Using default 'regex' option for now. Can be extended later.
        results = self.toolkit.bold_definitions_search_manager.search(
            search1=search_bold, search2=search_within, option="regex"
        )

        if not results:
            self.view.update_results([], "")
            return

        # Pass the first 50 results and the search term to the view
        self.view.update_results(results[:50], search_within)

    def clear_fields(self, e):
        self.view.clear_all_fields()
