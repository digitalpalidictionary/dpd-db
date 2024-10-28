import re
from rich import print


def generate_root_info_html(db_session, roots_db, bases_dict, show_ru_data=False):
    """Create an html table of all info specfic to a pali root."""
    print("[green]compiling root info")

    for counter, i in enumerate(roots_db):

        root_clean = re.sub(" \\d*$", "", i.root)
        root_group_pali = root_grouper(i.root_group)
        try:
            bases = ", ".join(sorted(bases_dict[i.root], key=len))
        except KeyError:
            bases = "-"

        html_string = ""
        html_string += "<table class='root_info'><tbody>"
        html_string += f"<tr><th>Pāḷi Root:</th><td>{root_clean}"
        html_string += f"<sup>{i.root_has_verb}</sup>"
        html_string += f"{i.root_group} {root_group_pali} + {i.root_sign}"
        html_string += f" ({i.root_meaning})</td></tr>"

        if show_ru_data:
            html_string += f"<tr><th><a class='root_link' href='https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&entry.438735500=${i.root_link}&entry.326955045=Инфо+корня&entry.1433863141=GoldenDict' target='_blank'>Русский:</a></th><td>{i.root_ru_meaning}</td></tr>"

        if re.findall(",", bases):
            html_string += f"<tr><th>Bases:</th><td>{bases}</td></tr>"
        else:
            html_string += f"<tr><th>Base:</th><td>{bases}</td></tr>"

        # Root in comps
        if i.root_in_comps:
            html_string += "<tr><th>Root in Compounds:</th>"
            html_string += f"<td>{i.root_in_comps}</td></tr>"

        # Dhātupātha
        if i.dhatupatha_root != "-":
            html_string += "<tr><th>Dhātupātha:</th>"
            html_string += f"<td>{i.dhatupatha_root} <i>{i.dhatupatha_pali}"
            html_string += f"</i> ({i.dhatupatha_english}) "
            html_string += f"#{i.dhatupatha_num}</td></tr>"
        else:
            html_string += "<tr><th>Dhātupātha:</th><td>-</td></tr>"

        # Dhātumañjūsa
        if i.dhatumanjusa_root != "-":
            html_string += "<tr><th>Dhātumañjūsa:</th>"
            html_string += f"<td>{i.dhatumanjusa_root} "
            html_string += f"<i>{i.dhatumanjusa_pali}</i> "
            html_string += f"({i.dhatumanjusa_english}) "
            html_string += f"#{i.dhatumanjusa_num}</td></tr>"
        else:
            html_string += "<tr><th>Dhātumañjūsa:</th><td>-</td></tr>"

        # Saddanīti
        if i.dhatumala_root != "-":
            html_string += "<tr><th>Saddanīti:</th>"
            html_string += f"<td>{i.dhatumala_root} <i>{i.dhatumala_pali}</i> "
            html_string += f"({i.dhatumala_english})</td></tr>"
        else:
            html_string += "<tr><th>Saddanīti:</th><td>-</td></tr>"

        # Sanskrit
        html_string += "<tr><th>Sanskrit Root:</th>"
        html_string += f"<td><span class='gray'>{i.sanskrit_root} "
        html_string += f"{i.sanskrit_root_class} "
        html_string += f"({i.sanskrit_root_meaning})"
        if show_ru_data:
            html_string += f" ({i.sanskrit_root_ru_meaning})"
        html_string += "</span></td></tr>"

        # Pāṇinīya Dhātupāṭha
        if i.panini_root != "-":
            html_string += "<tr><th>Pāṇinīya Dhātupāṭha:</th>"
            html_string += "<td><span class='gray'>"
            html_string += f"{i.panini_root} <i>{i.panini_sanskrit}</i> "
            html_string += f"({i.panini_english})</span></td></tr>"
        else:
            html_string += "<tr><th>Pāṇinīya Dhātupāṭha:</th><td>-</td></tr>"

        if i.note:
            html_string += f"<tr><th>Notes:</th><td>{i.note}</td></tr>"

        html_string += "</tbody></table>"

        i.root_info = html_string

        if counter % 100 == 0:
            print(
                f"{counter:>10,} / {len(roots_db):<10,} {i.root}")

    db_session.commit()


def root_grouper(root_group: int):
    """Convert numerical root group into pali name."""
    root_groups = {
        1: "bhūvādigaṇa",
        2: "rudhādigaṇa",
        3: "divādigaṇa",
        4: "svādigaṇa",
        5: "kiyādigaṇa",
        6: "gahādigaṇa",
        7: "tanādigaṇa",
        8: "curādigaṇa"
    }
    return root_groups.get(root_group, "ERROR!")
