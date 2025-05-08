from aksharamukha import transliterate

from tools.printer import printer as pr
from tools.pali_alphabet import pali_alphabet


def auto_translit_to_roman(text: str) -> str:
    if not text:
        return ""

    # If the first two characters are uppercase, return the text as is
    # e.g. DN1, DHPa
    if len(text) >= 2 and text[0].isupper() and text[1].isupper():
        return text

    # Pure Pāḷi gets a pass
    if text[0] in pali_alphabet:
        return text

    else:
        try:
            transliterated_text = transliterate.process(
                "autodetect", "IASTPali", text, post_options=["AnusvaratoNasalASTISO"]
            )
            if transliterated_text:
                transliterated_text = (
                    transliterated_text.replace("ï", "i")
                    .replace("ü", "u")
                    .replace("ĕ", "e")
                    .replace("ŏ", "o")
                    .replace("l̤", "ḷ")
                )
                return transliterated_text
            else:
                return text
        except Exception as e:
            print(f"Error during Aksharamukha transliteration: {e}")
            return text


def main():
    pr.green_title("transliterating timer")

    test_list = [
        ["māḷā"],
        ["dhamma", "धम्म", "ဓမ္မ", "ธมฺม", "ධම්ම"],
        ["buddha", "बुद्ध", "ဗုဒ္ဓ", "พุทฺธ", "බුද්ධ"],
        ["saṅgha", "सङ्घ", "သံဃ", "สงฺฆ", "සංඝ"],
        ["mettā", "मेत्ता", "မေတ္တာ", "เมตฺตา", "මෙත්තා"],
        ["anicca", "अनिच्च", "အနိစ္စ", "อนิจฺจ", "අනිච්ච"],
        ["dukkha", "दुक्ख", "ဒုက္ခ", "ทุกฺข", "දුක්ඛ"],
        ["anattā", "अनत्ता", "အနတ္တာ", "อนตฺตา", "අනත්තා"],
        ["kamma", "कम्म", "ကမ္မ", "กมฺม", "කම්ම"],
        ["nibbāna", "निब्बान", "နိဗ္ဗာန", "นิพฺพาน", "නිබ්බාන"],
        ["sīla", "सील", "သီလ", "สีล", "සීල"],
        ["samādhi", "समाधि", "သမာဓိ", "สมาธิ", "සමාධි"],
        ["paññā", "पञ्ञा", "ပညာ", "ปญฺญา", "පඤ්ඤා"],
        ["sutta", "सुत्त", "သုတ္တ", "สุตฺต", "සුත්ත"],
        ["bhikkhu", "भिक्खु", "ဘိက္ခု", "ภิกฺขุ", "භික්ඛු"],
        ["jhāna", "झान", "ဈာန", "ฌาน", "ඣාන"],
        ["vipassanā", "विपस्सना", "ဝိပဿနာ", "วิปสฺสนา", "විපස්සනා"],
        ["sacca", "सच्च", "သစ္စ", "สจฺจ", "සච්ච"],
        ["vinaya", "विनय", "ဝိနယ", "วินย", "විනය"],
        ["abhidhamma", "अभिधम्म", "အဘိဓမ္မ", "อภิธมฺม", "අභිධම්ම"],
        ["karuṇā", "करुणा", "ကရုဏာ", "กรุณา", "කරුණා"],
    ]
    counter = 1
    for index, list in enumerate(test_list):
        for word in list:
            roman = auto_translit_to_roman(word)
            pr.counter(counter, len(test_list), f"{roman}")
            counter += 1


if __name__ == "__main__":
    main()
