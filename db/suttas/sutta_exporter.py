from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from tools.goldendict_exporter import (
    DictEntry,
    DictInfo,
    DictVariables,
    export_to_goldendict_with_pyglossary,
)
from tools.mdict_exporter import export_to_mdict
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_dot_dict


@dataclass
class SuttaEntry:
    edited: str
    book: str
    book_code: str
    dpd_code: str
    dpd_sutta: str
    dpd_sutta_var: str
    cst_code: str
    cst_nikaya: str
    cst_book: str
    cst_section: str
    cst_vagga: str
    cst_sutta: str
    cst_paranum: str
    cst_m_page: str
    cst_v_page: str
    cst_p_page: str
    cst_t_page: str
    cst_file: str
    sc_code: str
    sc_book: str
    sc_vagga: str
    sc_sutta: str
    sc_eng_sutta: str
    sc_blurb: str
    sc_card_link: str
    sc_pali_link: str
    sc_eng_link: str
    sc_file_path: str


class SuttaExporter:
    def __init__(self):
        pr.tic()
        pr.title("exporting sutta information")
        self.pth = ProjectPaths()
        # TODO always fetch the latest from GoogleDocs
        self.sutta_file_path = Path("db/suttas/suttas.tsv")  # TODO add to ProjectPaths

        # jinja template
        self.env = Environment(loader=FileSystemLoader("."))
        self.template = self.env.get_template("db/suttas/suttas.html")
        # TODO add CSS to dpd.css
        self.css_path = Path("db/suttas/dpd-suttas.css")  # TODO add to ProjectPaths
        self.header_path = Path("db/suttas/sutta_header.html")
        self.header_html = Path.read_text(self.header_path)

        self.sutta_list: list[SuttaEntry] = read_tsv_dot_dict(self.sutta_file_path)

        self.make_dict_data()
        self.export_to_gdict_mdict()

        pr.toc()

    def make_dict_data(self):
        pr.green("making dict data")
        self.dict_data: list[DictEntry] = []

        for i in self.sutta_list:
            # only add if there's a dpd_code
            if i.dpd_code:
                html: str = self.header_html
                html += "<body>"
                html += str(self.template.render(i=i))
                html += "</body></html>"

                synonyms: list[str] = [
                    i.dpd_code,
                    i.dpd_sutta,
                    i.dpd_sutta_var,
                    i.sc_code,
                    i.sc_sutta,
                ]
                # TODO here need to add all known inflections

                self.dict_data.append(
                    DictEntry(
                        word=i.dpd_sutta,
                        definition_html=html,
                        definition_plain="",
                        synonyms=synonyms,
                    )
                )
        pr.yes(len(self.dict_data))

    def export_to_gdict_mdict(self):
        pass
        dict_info = DictInfo(
            bookname="DPD Suttas",
            author="Bodhirasa",
            description="<h3>DPD Suttas by Bodhirasa</h3><p>Detailed information on suttas.",
            website="",  # TODO add the docs link
            source_lang="pi",
            target_lang="eng",
        )

        dict_vars = DictVariables(
            css_paths=[self.css_path],
            js_paths=None,
            gd_path=self.pth.share_dir,
            md_path=self.pth.share_dir,
            dict_name="dpd-suttas",
            icon_path=None,  # TODO make an icon
            font_path=None,  # TODO add a font
            zip_up=False,
            delete_original=False,
        )

        export_to_goldendict_with_pyglossary(dict_info, dict_vars, self.dict_data)
        export_to_mdict(dict_info, dict_vars, self.dict_data)


def main():
    SuttaExporter()
    # TODO add to makedict and github workflows


if __name__ == "__main__":
    main()
