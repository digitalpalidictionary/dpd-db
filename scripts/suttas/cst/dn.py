"""Extract DN sutta rows from CST XML for the cst.tsv builder."""

from pathlib import Path

from bs4 import BeautifulSoup, Tag


def extract_dn_data(
    soup: BeautifulSoup, relative_path: Path
) -> list[dict[str, str | Path | None]]:
    """Extract CST rows for DN from a parsed CST XML file."""
    soup_chunks = soup.find_all(["div", "head", "p"])
    data_list: list[dict[str, str | Path | None]] = []
    current_id = None
    nikaya = None
    book = None
    # vagga = None
    # code = None
    paranum = None
    # page numbers
    m_page = None
    v_page = None
    p_page = None
    t_page = None

    for x in soup_chunks:
        if not isinstance(x, Tag):
            continue
        data: dict[str, str | Path | None] = {}

        if x.get("rend", "") == "nikaya":
            nikaya = x.text.strip()
        if x.get("rend", "") == "book":
            book = x.text.strip()
        if x.get("id", ""):
            current_id = str(x["id"]).replace("_", ".")
        if x.get("n", ""):
            n = str(x["n"]).replace("_", ".")
        if x.get("rend", "") == "chapter":
            sutta = x.text.strip()

            # Find the next paragraph containing paranum
            next_para = x.find_next("p", {"rend": "bodytext"})
            if next_para:
                paranum_tag = next_para.find("hi", {"rend": "paranum"})
                paranum = paranum_tag.text.strip() if paranum_tag else None

                # Find all pb elements in this paragraph
                pbs = next_para.find_all("pb")
                for pb in pbs:
                    ed = pb.get("ed")
                    n = str(pb.get("n"))
                    if ed == "M":
                        m_page = n
                    elif ed == "V":
                        v_page = n
                    elif ed == "P":
                        p_page = n
                    elif ed == "T":
                        t_page = n

            data["cst_code"] = current_id
            data["cst_nikaya"] = nikaya
            data["cst_book"] = book
            data["cst_section"] = ""
            data["cst_vagga"] = ""
            data["cst_sutta"] = sutta
            data["cst_paranum"] = paranum
            data["cst_m_page"] = m_page
            data["cst_v_page"] = v_page
            data["cst_p_page"] = p_page
            data["cst_t_page"] = t_page
            data["cst_file"] = relative_path

            data_list.append(data)

    return data_list
