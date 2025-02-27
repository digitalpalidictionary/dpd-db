def process_links(sc_data):
    base_url = "https://suttacentral.net"

    for code in sc_data:
        sc_card_link = base_url + f"/{code}"
        sc_pali_link = base_url + f"/{code}/pli/ms"
        sc_eng_link = base_url + f"/{code}/en/sujato"

        sc_data[code]["sc_card_link"] = sc_card_link
        sc_data[code]["sc_pali_link"] = sc_pali_link
        sc_data[code]["sc_eng_link"] = sc_eng_link

    return sc_data
