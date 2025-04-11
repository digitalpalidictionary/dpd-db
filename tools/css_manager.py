"""
Create a Single Source of Truth for all CSS files.
1. WebApp
2. All GoldenDict exporters
3. MkDocs
"""

from tools.paths import ProjectPaths


class CSSManager:
    def __init__(self):
        self.pth: ProjectPaths = ProjectPaths()
        self.dpd_css: str = self.pth.dpd_css_path.read_text()
        self.dpd_css_variables: str = self.pth.dpd_css_variables_path.read_text()
        self.dpd_css_fonts: str = self.pth.dpd_css_fonts_path.read_text()
        self.new_style = f"""
<style>
{self.dpd_css_fonts}

{self.dpd_css_variables}

"""

    def update_webapp_css(self) -> None:
        """The WebApp needs variables and dpd.css."""

        css_list: list[str] = []
        css_list.append(self.dpd_css_variables)
        css_list.append("")
        css_list.append(self.dpd_css)

        css_file = "\n".join(css_list)
        self.pth.webapp_css_path.write_text(css_file)

    def update_style(self, header: str):
        """Replace the style in header with fonts and variables."""
        return header.replace("<style>", self.new_style)

    def update_docs_css(self):
        """Save the CSS Variables to the docs folder."""
        self.pth.docs_css_variables_path.write_text(self.dpd_css_variables)


if __name__ == "__main__":
    css_manager = CSSManager()
    css_manager.update_docs_css()
    css_manager.update_webapp_css()
