import re


def get_text_and_number(text: str) -> tuple[str, str]:
    """
    '2. Appamādavaggo' > ('Appamādavaggo', 2)
    """
    clean = re.sub(r"^\d.*\. *", "", text)
    clean_no = re.sub(r"\. .+", "", text)
    return clean, clean_no


def get_text_and_number_with_brackets1(text: str) -> tuple[str, str]:
    """
    '(1) Mahāvaggo' > ('Mahāvaggo', 1)
    """
    clean = re.sub(r"^\(\d*\) *", "", text)
    clean_no = re.sub(r"\(|\).+", "", text)
    return clean, clean_no


def get_text_and_number_with_brackets2(text: str) -> tuple[str, str]:
    """
    '(7) 2. Sukhavaggo' > ('Sukhavaggo', 2)
    """
    text = re.sub(r"^\(\d*\)\.* *", "", text)
    clean, clean_no = get_text_and_number(text)
    return clean, clean_no


def get_text_and_number_with_brackets3(text: str) -> tuple[str, str]:
    """
    '(12) 3. Kaṅkhākathā' > ('Kaṅkhākathā', 12)
    """
    clean = re.sub(r"^.+\. ", "", text)
    clean_no = re.sub(r"\(|\).+", "", text)
    return clean, clean_no


def get_text_and_number_with_brackets_end(text: str) -> tuple[str, str]:
    """
    '153. Sūkarajātakaṃ (2-1-3)' > ('Sūkarajātakaṃ', 153)
    """
    text = re.sub(r" \(\d.*\)", "", text)
    clean, clean_no = get_text_and_number(text)
    return clean, clean_no


def get_text_and_number_with_brackets_abhidhamma(text: str) -> tuple[str, str]:
    """
    '(26. Ka) dovacassatā' > ('dovacassatā', 26)

    """
    clean = re.sub(r"^\(.*\) *", "", text)
    clean_no = re.sub(r"\(|[^0-9]|\).+", "", text)
    return clean, clean_no


def get_text_and_number_ana(text: str) -> tuple[str, str]:
    sutta = re.sub(r"^.+\. ", "", text)
    sutta_no = re.sub(r"^\(|\).+|\..+", "", text)
    return sutta, sutta_no


def get_text_and_number_with_sqaure_brackets(text: str) -> tuple[str, str]:
    """
    '[111] 1. Gadrabhapañhajātakavaṇṇanā' > ('Gadrabhapañhajātakavaṇṇanā', 111)
    """
    sutta = re.sub(r".+\. ", "", text)
    sutta_no = re.sub(r"\[|\].+", "", text)
    return sutta, sutta_no


def clean_subtitle(text: str) -> str:
    """
    '(7-8) Karacaraṇamudujālatālakkhaṇāni' >
    'Karacaraṇamudujālatālakkhaṇāni'
    """
    return re.sub(r"\(.*\) ", "", text)


def clean_example(text: str) -> str:
    text = text.strip()
    text = text.lower()
    text = text.replace("‘", "")
    text = text.replace(" – ", ", ")
    text = text.replace("’", "")
    text = text.replace("…pe॰…", " … ")
    text = text.replace("…pe…", " … ")
    text = text.replace(";", ",")
    text = text.replace("  ", " ")
    text = text.replace("..", ".")
    text = text.replace(" ,", ",")

    # remove abbreviations in brackets, no more than 20 characters
    text = re.sub(r" \([^)]{0,20}\.\)", "", text)

    return text


def clean_gatha(text: str) -> str:
    text = clean_example(text)
    text = text.strip()
    text = text.replace(" ,", ",")
    text = text.replace(" .", ".")
    text = text.replace(", ", ",\n")
    text = re.sub(",$", ",\n", text)
    return text


def assert_type_int(text: str) -> str:
    try:
        int(text)
        return text
    except (ValueError, TypeError):
        return ""


def is_int(text: str) -> bool:
    try:
        if isinstance(int(text), int):
            return True
        else:
            return False
    except Exception:
        return False


def assert_no_space(sutta_name: str) -> str:
    try:
        assert " " not in sutta_name
        return sutta_name
    except (TypeError, AssertionError):
        return ""


def split_sutta_number(text: str) -> tuple[int, int, int]:
    """1-4 > (1, 4, 4)"""
    start = int(re.sub("-.*", "", text))
    end = int(re.sub(r"^\d*-|\.*", "", text))
    return start, end, end - start + 1
