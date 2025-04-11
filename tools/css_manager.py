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
        self.dpd_variables: str = self.pth.dpd_variables_css_path.read_text()
        self.dpd_fonts: str = self.pth.dpd_fonts_css_path.read_text()
        self.new_style = f"""
<style>
{self.dpd_variables}
"""

    def update_webapp_css(self) -> None:
        """The WebApp needs variables and dpd.css. No fonts in the CSS."""

        css_list: list[str] = []
        css_list.append(self.dpd_variables)
        css_list.append("")
        css_list.append(self.dpd_css)

        css_file = "\n".join(css_list)
        self.pth.webapp_css_path.write_text(css_file)

    def update_style(self, header: str):
        """Replace the style in exporter headers with fonts and variables."""
        return header.replace("<style>", self.new_style)

    def update_docs_css(self):
        """Save the CSS Variables to the docs folder."""
        self.pth.docs_css_variables_path.write_text(self.dpd_variables)

    def compile_css_and_fonts(self):
        """Compile CSS and fonts into one for GoldenDict exporters."""
        css_and_fonts_list = []
        css_and_fonts_list.append(self.dpd_fonts)
        css_and_fonts_list.append("")
        css_and_fonts_list.append(self.dpd_css)
        css_and_fonts_str = "\n".join(css_and_fonts_list)
        self.pth.dpd_css_and_fonts_path.write_text(css_and_fonts_str)

if __name__ == "__main__":
    css_manager = CSSManager()
    css_manager.update_docs_css()
    css_manager.update_webapp_css()
    css_manager.compile_css_and_fonts()
