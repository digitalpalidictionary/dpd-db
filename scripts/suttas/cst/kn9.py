from scripts.suttas.cst.modules import get_sutta_num


def extract_kn9_data(soup, relative_path):
    data_list = []

    soup_chunks = soup.find_all(["div", "head", "p"])
    id = None
    nikaya = None
    book = None
    section = None
    vagga = None
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

        if x.get("rend") == "chapter":
            vagga = x.text.strip()

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

        if x.get("rend") == "subhead":
            note = x.find("note")
            if note:
                note.extract()
            sutta = x.text.strip()
            sutta_num = get_sutta_num(x)
            code = f"{id}.{sutta_num}"

            # Find the next paragraph containing paranum
            next_para = x.find_next("p")
            if next_para:
                paranum = next_para.find("hi", {"rend": "paranum"})
                if paranum:
                    paranum = paranum.text.strip()

                # Find all pb elements in this paragraph
                pbs = next_para.find_all("pb")
                if (
                    m_page is None or v_page is None or p_page is None or t_page is None
                ) or (
                    pb.previous_sibling is None
                    or (
                        pb.previous_sibling.name == "hi"
                        and pb.previous_sibling.get("rend") == "paranum"
                    )
                ):
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

            data["cst_code"] = code
            data["cst_nikaya"] = nikaya
            data["cst_book"] = book
            data["cst_section"] = section
            data["cst_vagga"] = vagga
            data["cst_sutta"] = sutta
            data["cst_paranum"] = paranum
            data["cst_m_page"] = m_page
            data["cst_v_page"] = v_page
            data["cst_p_page"] = p_page
            data["cst_t_page"] = t_page
            data["cst_file"] = relative_path
            data_list.append(data)

    return data_list
