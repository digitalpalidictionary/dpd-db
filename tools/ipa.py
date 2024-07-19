"""Convert Pāḷi text to IPA"""

from pathlib import Path
import re
from rich import print

from tools.tsv_read_write import read_tsv_dot_dict
from tools.tsv_read_write import write_tsv_dot_dict


class ProgData():
    def __init__(self) -> None:
        self.file_path: Path = Path("tools/ipa.tsv")
        self.tsv: list = read_tsv_dot_dict(self.file_path)
        self.uni_to_ipa_dict: dict = self.make_uni_to_ipa_dict(self.tsv)
        self.uni_to_tts_dict: dict = self.make_uni_to_tts_dict(self.tsv)

    def make_uni_to_ipa_dict(self, tsv):
        dict = {}
        for i in tsv:
            if i.section == "unused":
                break
            if i.ipa:
                dict[i.unicode] = i.ipa
        return dict

    def make_uni_to_tts_dict(self, tsv):
        dict = {}
        for i in tsv:
            if i.section == "unused":
                break
            if i.tts:
                dict[i.unicode] = i.tts
            else:
                dict[i.unicode] = i.ipa
        return dict


def update_tsv():
    g = ProgData()
    for i in g.tsv:
        i.ipa_eg = convert_uni_to_ipa(i.unicode_eg, "ipa")
        i.tts_eg = convert_uni_to_ipa(i.unicode_eg, "tts")
    write_tsv_dot_dict(g.file_path, g.tsv)


double_consonants = [
        "kk", "gg", "ṅṅ", 
        "cc", "jj", "ññ", 
        "ṭṭ", "ḍḍ", "ṇṇ", 
        "tt", "dd", "nn", 
        "pp", "bb", "mm", 
        "yy", "rr", "ll", 
        "ss", "vv", "ḷḷ", 
        "jv", "tv", "dv", 
        "hm", 
        "kr", "tr", "dr",
        "pr", "br", 
        "nt", "mt", 
]


def clean_text(text: str):
  return text \
  .replace(".", "") \
  .replace("'", "") \
  .replace("“", "") \
  .replace("”", "") \
  .replace("‘", "") \
  .replace("’", "") \
  .replace(",", "") \
  .replace(";" ,"") \
  .replace("—" ,"") \
  .replace("?" ,"") \
  .replace("  " ," ") \
  .lower()


def long_e_o(text: str):
    text = text.replace("e", "ē").replace("o", "ō")
    modified_text = ""

    for i in range(len(text)):
        current_letter = text[i]
        if (
            current_letter == "ē"
            or current_letter == "ō"
        ):
            following_letters = text[i+1:i+3]
            if following_letters in double_consonants:
                if current_letter == 'ē':
                    modified_text += "e"
                elif current_letter == "ō":
                    modified_text += "o"
            else:
                modified_text += current_letter
        else:
            modified_text += current_letter
        
    return modified_text


def a_at_the_end(text: str):
    return re.sub(
        "(a |a$)",
        "ə ",            
        text,
    )


def convert_uni_to_ipa(text:str, ipa_or_tts: str):
    """Use the "ipa" option to return academic IPA
    or the "tts" option to return IPA for text-to-speech-engines."""

    g = ProgData()

    if ipa_or_tts == "ipa":
        dict = g.uni_to_ipa_dict
    elif ipa_or_tts == "tts":
        dict = g.uni_to_tts_dict
    text = clean_text(text)
    text = long_e_o(text)
    text = a_at_the_end(text)

    ipa_text = ''
    i = 0
    while i < len(text):
        if i < len(text) - 2 and text[i:i+3] in dict:
            ipa_text += dict[text[i:i+3]]
            i += 3
        elif i < len(text) - 1 and text[i:i+2] in dict:
            ipa_text += dict[text[i:i+2]]
            i += 2
        elif text[i] in dict:
            ipa_text += dict[text[i]]
            i += 1
        else:
            ipa_text += text[i]
            i += 1
    
    ipa_text = ipa_text.strip().replace("  ", " ")
    return ipa_text


if __name__ == "__main__":
    update_tsv()
    text = "iti kira, vāseṭṭha, sapariggahā tevijjā brāhmaṇā apariggaho brahmā. api nu kho sapariggahānaṃ tevijjānaṃ brāhmaṇānaṃ apariggahena brahmunā saddhiṃ saṃsandati sametī”ti? “no hidaṃ, bho gotama”. “sādhu, vāseṭṭha, te vata, vāseṭṭha, sapariggahā tevijjā brāhmaṇā kāyassa bhedā paraṃ maraṇā apariggahassa brahmuno sahabyūpagā bhavissantī”ti, netaṃ ṭhānaṃ vijjati."
    ipa = convert_uni_to_ipa(text, "ipa")
    tts = convert_uni_to_ipa(text, "tts")
    print(f"[white]{text}")
    print(f"[green]{ipa}")
    print(f"[cyan]{tts}")    