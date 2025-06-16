# -*- coding: utf-8 -*-
"""
1. Create a Single Source of Truth for all CSS files.
    1. WebApp
    2. All GoldenDict exporters
    3. MkDocs

2. Dynamically update the headers of all exported dictionary with the correct variables.
"""

import re

from tools.paths import ProjectPaths


class CSSManager:
    def __init__(self):
        self.pth: ProjectPaths = ProjectPaths()
        self.dpd_css: str = self.pth.dpd_css_path.read_text()
        self.dpd_variables: str = self.pth.dpd_variables_css_path.read_text()
        self.dpd_fonts: str = self.pth.dpd_fonts_css_path.read_text()
        self.variables_reduced = self.dpd_variables

    def update_webapp_css(self) -> None:
        """The WebApp needs variables and dpd.css. No fonts in the CSS."""

        css_list: list[str] = []
        css_list.append(self.dpd_variables)
        css_list.append("")
        css_list.append(self.dpd_css)

        css_file = "\n".join(css_list)
        self.pth.webapp_css_path.write_text(css_file)

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

    def update_style(self, header: str, used_for: str):
        """
        Replace the style in exporter headers with fonts and variables.

        `used_for` values can be
        - `primary`: grammar_dict, spelling, epd
        - `secondary`: help and abbreviations
        - `dpd`: main dict
        - `root`: root dict
        - `variants`: variant dict
        """

        self.reduce_style(used_for)
        self.new_style = f"""
<style>
{self.variables_reduced}
"""
        # print(self.new_style)
        return header.replace("<style>", self.new_style)

    def reduce_style(self, used_for):
        """Based on `used_for`, strip away unnecessary variables"""

        if used_for == "primary":
            self._remove_all_except(["--primary"])
        if used_for == "secondary":
            self._remove_all_except(["--secondary"])
        if used_for == "dpd":
            self._remove_comments_and_whitespace()
            self._remove_only(["shade"])
        if used_for == "root":
            self._remove_all_except(["--primary", "--gray"])
        if used_for == "variants":
            self._remove_all_except(["--primary", "--gray"])
            self._remove_only(["--gray-light", "--gray-dark"])

    def _remove_all_except(self, variables: list[str]):
        """Remove all variables except the ones in the list."""

        lines = self.variables_reduced.splitlines()
        # leave lines with {} and the necessary variable
        lines = [
            line
            for line in lines
            if any(variable in line for variable in variables)
            or ("{" in line or "}" in line)
        ]
        self.variables_reduced = "\n".join(lines)

    def _remove_only(self, variables: list[str]):
        """Only remove the variables in the list."""

        lines = self.variables_reduced.splitlines()
        for variable in variables:
            # leave lines with {} and without necessary variable
            lines = [
                line
                for line in lines
                if variable not in line or ("{" in line or "}" in line)
            ]
        self.variables_reduced = "\n".join(lines)

    def _remove_comments_and_whitespace(self):
        "Strip away comments and empty lines."

        self.variables_reduced = re.sub(r"/\*[\s\S]*?\*/", "", self.variables_reduced)
        lines = self.variables_reduced.splitlines()
        lines = [line for line in lines if line.strip()]
        self.variables_reduced = "\n".join(lines)


if __name__ == "__main__":
    css_manager = CSSManager()
    css_manager.update_docs_css()
    css_manager.update_webapp_css()
    css_manager.compile_css_and_fonts()
    # new_style = css_manager.update_style("<style>", "secondary")
    # print(new_style)
