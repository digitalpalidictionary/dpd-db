
import json


def make_dpr_breakup_dict(PTH):
    print(f"[green]{'making dpr breakup dict':<40}", end="")
    with open(PTH.dpr_breakup) as f:
        dpr_breakup = json.load(f)

    dpr_breakup_dict = {}

    for headword, breakup in dpr_breakup.items():
        html = "<div class='dpr'>"
        html += "<h4 class='dpr'>DPR Analysis</h4>"
        html += "<p class='sandhi'>"
        html += breakup     # .replace(" (", "<br>(")
        html += "</p></div>"
        dpr_breakup_dict[headword] = html

    print(f"{len(dpr_breakup_dict):>10,}")

    return dpr_breakup_dict
