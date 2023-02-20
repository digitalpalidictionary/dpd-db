import re


def superscripter_html(text):
    """superscipt using html <sup>"""

    text = re.sub("( \\d.*$)", "<sup style='font-size: 75%;'>\\1</sup>", text)
    return text


def superscripter_uni(text):
    """superscipt using unicode characters"""
    text = re.sub("( )(\\d)", "\u200A\\2", text)
    text = re.sub("0", "⁰", text)
    text = re.sub("1", "¹", text)
    text = re.sub("2", "²", text)
    text = re.sub("3", "³", text)
    text = re.sub("4", "⁴", text)
    text = re.sub("5", "⁵", text)
    text = re.sub("6", "⁶", text)
    text = re.sub("7", "⁷", text)
    text = re.sub("8", "⁸", text)
    text = re.sub("9", "⁹", text)
    text = re.sub("\\.", "·", text)
    return text


def main():
    uni = superscripter_uni("""āsava 1.1""")
    html = superscripter_html("""āsava 1.1""")
    print(uni)
    print(html)


if __name__ == "__main__":
    main()
