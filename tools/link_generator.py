"""Generating links for suttas based on the desired website"""

import re
from tools.configger import config_test_option, config_update_default_value, config_read


def load_link():
    if not config_test_option("dictionary", "link_url"):
        config_update_default_value("dictionary", "link_url")
    return config_read("dictionary", "link_url")


base_url = load_link()


def generate_link(source: str) -> str:
    # List of functions to check each pattern
    pattern_funcs = [
        link_vin,
        link_vin_pat,
        link_pat,
        link_dn_mn,
        link_an,
        link_sn,
        link_khp,
        link_dhp,
        link_snp,
        link_ud,
        link_iti,
        link_thi,
        link_th,
    ]

    # Iterate over each function and return the first valid URL
    for func in pattern_funcs:
        url = func(source, base_url)
        if url:
            return url

    return ""


def link_vin(source: str, base_url: str) -> str:
    # Vinaya piṭaka
    # Logic for Bhikkhu Vibhanga
    source = source.strip().upper()
    if re.match(r"^(VIN\s?1|VIN\s?2).*", source):
        # Logic for VIN verses
        vin_match = re.match(r"VIN\s?(\d+)(\.(\d+))?(\.(\d+))?(\.(\d+))?", source)
        if vin_match:
            vin_main = int(vin_match.group(1))
            vin_sub1 = int(vin_match.group(3)) if vin_match.group(3) else None
            vin_sub2 = int(vin_match.group(5)) if vin_match.group(5) else None
            vin_sub3 = int(vin_match.group(7)) if vin_match.group(7) else None

            if vin_main == 1:
                if vin_sub1 == 0:
                    return f"{base_url}vi/bu-vb-pj1.html"
                elif vin_sub1 == 1 and vin_sub2 is not None:
                    return f"{base_url}vi/bu-vb-pj{vin_sub2}.html"
                elif vin_sub1 == 2 and vin_sub2 is not None:
                    return f"{base_url}vi/bu-vb-sn{vin_sub2}.html"
                elif vin_sub1 == 3 and vin_sub2 is not None:
                    return f"{base_url}vi/bu-vb-an{vin_sub2}.html"
                elif vin_sub1 == 4 and vin_sub2 is not None and vin_sub3 is not None:
                    index = (vin_sub2 - 1) * 10 + vin_sub3
                    return f"{base_url}vi/bu-vb-np{index}.html"
            # Handle other VIN 1.x cases if necessary

            elif vin_main == 2:
                if vin_sub1 == 5:
                    if vin_sub2 is not None and vin_sub3 is not None:
                        if 1 <= vin_sub2 <= 8:
                            index = (vin_sub2 - 1) * 10 + vin_sub3
                            return f"{base_url}vi/bu-vb-pc{index}.html"
                        elif vin_sub2 == 9:
                            index = 82 + vin_sub3
                            return f"{base_url}vi/bu-vb-pc{index}.html"
                elif vin_sub1 == 6 and vin_sub2 is not None:
                    if 1 <= vin_sub2 <= 4:
                        return f"{base_url}vi/bu-vb-pd{vin_sub2}.html"
                elif vin_sub1 == 7:
                    return f"{base_url}vi/bu-vb-sk.html"

        # If VIN not matched, return None or a default value
        return ""

    # VIN 4,5 cases
    elif re.match(r"^(VIN\s?4|VIN\s?5).*", source):
        return base_url + "vi/kd.html"

    return ""


def link_vin_pat(source: str, base_url: str) -> str:
    # Logic for VIN PAT
    vin_pat_match = re.match(r"VIN PAT (PA|SA|AN|NP|PC|PD|SE|AS)(?: (\d+))?", source)
    if vin_pat_match:
        pat_code, pat_number = vin_pat_match.groups()
        vin_pat_map = {
            "PA": "pr",
            "SA": "sg",
            "AN": "ay",
            "NP": "np",
            "PC": "pc",
            "PD": "pd",
            "SE": "sk",
            "AS": "as",
        }
        return f"{base_url}vi/bu-pt.html#{vin_pat_map[pat_code]}"

    return ""


def link_pat(source: str, base_url: str) -> str:
    # Logic for VIN PAT
    pattern = re.match(r"(PA|SA|NP|PC|PD|SE|AS)\s?(\d+)", source)
    if pattern:
        pat_code, pat_number = pattern.groups()
        vin_pat_map = {
            "PA": "pr",
            "SA": "sg",
            "NP": "np",
            "PC": "pc",
            "PD": "pd",
            "SE": "sk",
            "AS": "as",
        }
        return f"{base_url}vi/bu-pt.html#{vin_pat_map[pat_code]}"

    return ""


def link_dn_mn(source: str, base_url: str) -> str:
    match = re.match(r"(DN|MN)\s?(\d+)(\.\d+)?", source)
    if match:
        book, number = match.groups()[0], match.groups()[1]
        return f"{base_url}{book.lower()}/{book.lower()}{number}.html"

    return ""


def link_an(source: str, base_url: str) -> str:
    # Special case for AN3.x
    an_match = re.match(r"AN\s?3\.(\d+)", source)
    if an_match:
        sub_num = int(an_match.group(1))
        if 48 <= sub_num <= 183:
            sub_num -= 1
        return f"{base_url}an/an3.{sub_num}.html"

    return ""


def link_sn(source: str, base_url: str) -> str:
    # Regular cases for AN, SN (whole number valid with sub numbers)
    sub_match = re.match(r"(AN|SN)\s?(\d+(\.\d+)?)", source)
    if sub_match:
        book, number = sub_match.groups()[0], sub_match.groups()[1]
        return f"{base_url}{book.lower()}/{book.lower()}{number}.html"

    return ""


def link_khp(source: str, base_url: str) -> str:
    # Logic for KHP verses
    khp_match = re.match(r"KHP\s?(\d+)", source)
    if khp_match:
        khp_number = int(khp_match.group(1))
        return f"{base_url}kp/kp{khp_number}.html"

    return ""


# Example of a more data-driven approach:
def link_dhp(source: str, base_url: str) -> str:
    match = re.match(r"DHP\s?(\d+)", source)
    if match:
        verse_number = int(match.group(1))
        dhp_ranges = {
            (1, 20): "dhp1-20.html",
            (21, 32): "dhp21-32.html",
            (33, 43): "dhp33-43.html",
            (44, 59): "dhp44-59.html",
            (60, 75): "dhp60-75.html",
            (76, 89): "dhp76-89.html",
            (90, 99): "dhp90-99.html",
            (100, 115): "dhp100-115.html",
            (116, 128): "dhp116-128.html",
            (129, 145): "dhp129-145.html",
            (146, 156): "dhp146-156.html",
            (157, 166): "dhp157-166.html",
            (167, 178): "dhp167-178.html",
            (179, 196): "dhp179-196.html",
            (197, 208): "dhp197-208.html",
            (209, 220): "dhp209-220.html",
            (221, 234): "dhp221-234.html",
            (235, 255): "dhp235-255.html",
            (256, 272): "dhp256-272.html",
            (273, 289): "dhp273-289.html",
            (290, 305): "dhp290-305.html",
            (306, 319): "dhp306-319.html",
            (320, 333): "dhp320-333.html",
            (334, 359): "dhp334-359.html",
            (360, 382): "dhp360-382.html",
            (383, 423): "dhp383-423.html",
        }
        for (start, end), url_suffix in dhp_ranges.items():
            if start <= verse_number <= end:
                return base_url + "dhp/" + url_suffix

    return ""


def link_snp(source: str, base_url: str) -> str:
    # Logic for SNP verses
    snp_match = re.match(r"SNP\s?(\d+)", source)
    if snp_match:
        snp_number = int(snp_match.group(1))

        if 1 <= snp_number <= 12:
            return base_url + f"snp/snp1.{snp_number}.html"
        elif 13 <= snp_number <= 26:
            return base_url + f"snp/snp2.{snp_number - 12}.html"
        elif 27 <= snp_number <= 38:
            return base_url + f"snp/snp3.{snp_number - 26}.html"
        elif 39 <= snp_number <= 54:
            return base_url + f"snp/snp4.{snp_number - 38}.html"
        elif 55 <= snp_number <= 71:
            return base_url + f"snp/snp5.{snp_number - 54}.html"
        elif snp_number in [72, 73]:
            return base_url + "snp/snp5.18.html"

    return ""


def link_ud(source: str, base_url: str) -> str:
    # Logic for UD verses
    ud_match = re.match(r"UD\s?(\d+)", source)
    if ud_match:
        ud_number = int(ud_match.group(1))
        if 1 <= ud_number <= 10:
            return f"{base_url}ud/ud1.{ud_number}.html"
        elif 11 <= ud_number <= 20:
            return f"{base_url}ud/ud2.{ud_number - 10}.html"
        elif 21 <= ud_number <= 30:
            return f"{base_url}ud/ud3.{ud_number - 20}.html"
        elif 31 <= ud_number <= 40:
            return f"{base_url}ud/ud4.{ud_number - 30}.html"
        elif 41 <= ud_number <= 50:
            return f"{base_url}ud/ud5.{ud_number - 40}.html"
        elif 51 <= ud_number <= 60:
            return f"{base_url}ud/ud6.{ud_number - 50}.html"
        elif 61 <= ud_number <= 70:
            return f"{base_url}ud/ud7.{ud_number - 60}.html"
        elif 71 <= ud_number <= 80:
            return f"{base_url}ud/ud8.{ud_number - 70}.html"

    return ""


def link_iti(source: str, base_url: str) -> str:
    # Logic for ITI verses
    if source.startswith("ITI"):
        return base_url + "it/it.html"

    return ""


def link_thi(source: str, base_url: str) -> str:
    # Logic for THI verses
    thi_match = re.match(r"THI\s?(\d+)", source)
    if thi_match:
        thi_number = int(thi_match.group(1))
        if 1 <= thi_number <= 18:
            return f"{base_url}thi/thi1.html"
        elif 19 <= thi_number <= 28:
            return f"{base_url}thi/thi2.html"
        elif 29 <= thi_number <= 36:
            return f"{base_url}thi/thi3.html"
        elif thi_number == 37:
            return f"{base_url}thi/thi4.html"
        elif 38 <= thi_number <= 49:
            return f"{base_url}thi/thi5.html"
        elif 50 <= thi_number <= 57:
            return f"{base_url}thi/thi6.html"
        elif 58 <= thi_number <= 60:
            return f"{base_url}thi/thi7.html"
        elif thi_number == 61:
            return f"{base_url}thi/thi8.html"
        elif thi_number == 62:
            return f"{base_url}thi/thi9.html"
        elif thi_number == 63:
            return f"{base_url}thi/thi10.html"
        elif thi_number == 64:
            return f"{base_url}thi/thi11.html"
        elif thi_number == 65:
            return f"{base_url}thi/thi12.html"
        elif 66 <= thi_number <= 70:
            return f"{base_url}thi/thi13.html"
        elif thi_number == 71:
            return f"{base_url}thi/thi14.html"
        elif thi_number == 72:
            return f"{base_url}thi/thi15.html"
        elif thi_number == 73:
            return f"{base_url}thi/thi16.html"

    return ""


def link_th(source: str, base_url: str) -> str:
    # Logic for TH verses
    th_match = re.match(r"TH\s?(\d+)", source)
    if th_match:
        th_number = int(th_match.group(1))
        if 1 <= th_number <= 120:
            return f"{base_url}tha/tha1.html"
        elif 121 <= th_number <= 169:
            return f"{base_url}tha/tha2.html"
        elif 170 <= th_number <= 185:
            return f"{base_url}tha/tha3.html"
        elif 186 <= th_number <= 197:
            return f"{base_url}tha/tha4.html"
        elif 198 <= th_number <= 209:
            return f"{base_url}tha/tha5.html"
        elif 210 <= th_number <= 223:
            return f"{base_url}tha/tha6.html"
        elif 224 <= th_number <= 228:
            return f"{base_url}tha/tha7.html"
        elif 229 <= th_number <= 231:
            return f"{base_url}tha/tha8.html"
        elif th_number == 232:
            return f"{base_url}tha/tha9.html"
        elif 233 <= th_number <= 239:
            return f"{base_url}tha/tha10.html"
        elif th_number == 240:
            return f"{base_url}tha/tha11.html"
        elif 241 <= th_number <= 242:
            return f"{base_url}tha/tha12.html"
        elif th_number == 243:
            return f"{base_url}tha/tha13.html"
        elif 244 <= th_number <= 245:
            return f"{base_url}tha/tha14.html"
        elif 246 <= th_number <= 247:
            return f"{base_url}tha/tha15.html"
        elif 248 <= th_number <= 257:
            return f"{base_url}tha/tha16.html"
        elif 258 <= th_number <= 260:
            return f"{base_url}tha/tha17.html"
        elif th_number == 261:
            return f"{base_url}tha/tha18.html"
        elif th_number == 262:
            return f"{base_url}tha/tha19.html"
        elif th_number == 263:
            return f"{base_url}tha/tha20.html"
        elif th_number == 264:
            return f"{base_url}tha/tha21.html"

    return ""
