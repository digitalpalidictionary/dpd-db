import re

from icecream import ic

from scripts.suttas.cst.modules import extract_sutta_data


def extract_mn_data(soup):
    data_list = []

    soup_chunks = soup.find_all(["div", "head", "p"])
    id = None
    nikaya = None
    book = None
    vagga = None
    code = None
    paranum = None
    # page numbers
    m_page = None
    v_page = None
    p_page = None
    t_page = None

    for x in soup_chunks:
        data = {}

        if x.get("rend", "") == "nikaya":
            nikaya = x.text.strip()

        if x.get("rend", "") == "book":
            book = x.text.strip()

        if x.get("id", ""):
            id = x["id"].replace("_", ".")

        if x.get("n", ""):
            n = x["n"].replace("_", ".")

        if x.get("rend", "") == "chapter":
            vagga = re.sub(r"\d*\. ", "", x.text.strip())

        if x.name == "p":
            pbs = x.find_all("pb")
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

        if (
            x.get("rend") == "subhead"
            # suttas always start with a number, subsections don't
            and re.match(r"\d*\. ", x.text.strip())
        ):
            sutta = re.sub(r"\d*\. ", "", x.text.strip())
            sutta_num = re.sub(r"\. .+", "", x.text.strip())
            code = f"{id}.{sutta_num}"

            # Find the next paragraph containing paranum
            next_para = x.find_next("p", {"rend": "bodytext"})
            if next_para:
                paranum = next_para.find("hi", {"rend": "paranum"})
                if paranum:
                    paranum = paranum.text.strip()

                # Find all pb elements in this paragraph
                pbs = next_para.find_all("pb")
                for pb in pbs:
                    # Check if pb is at the start of the paragraph
                    if (
                        m_page is None
                        or v_page is None
                        or p_page is None
                        or t_page is None
                    ) or (
                        pb.previous_sibling is None
                        or (
                            pb.previous_sibling.name == "hi"
                            and pb.previous_sibling.get("rend") == "paranum"
                        )
                    ):
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

            data["code"] = code
            data["nikaya"] = nikaya
            data["book"] = book
            data["samyutta"] = "-"
            data["fifty"] = "-"
            data["vagga"] = vagga
            data["sutta"] = sutta
            data["paranum"] = paranum
            data["m_page"] = m_page
            data["v_page"] = v_page
            data["p_page"] = p_page
            data["t_page"] = t_page
            data_list.append(data)

    return data_list


if __name__ == "__main__":
    file_list = ["mn1", "mn2", "mn3"]
    output_tsv = "scripts/suttas/cst/mn.tsv"
    extract_sutta_data(file_list, output_tsv, extract_mn_data)
