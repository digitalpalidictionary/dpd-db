def extract_dn_data(soup, relative_path):
    soup_chunks = soup.find_all(["div", "head", "p"])
    data_list = []
    id = None
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
            sutta = x.text.strip()

            # Find the next paragraph containing paranum
            next_para = x.find_next("p", {"rend": "bodytext"})
            if next_para:
                paranum = next_para.find("hi", {"rend": "paranum"})
                if paranum:
                    paranum = paranum.text.strip()

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

            data["cst_code"] = id
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
