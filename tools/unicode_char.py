def unicode_char(text):
    # convert int to str
    if isinstance(text, int):
        text = str(text)

    # str > ord > unicode
    unicode_string = ""
    for char in text:
        unicode_string += "\\u{:04x}".format(ord(char))

    return unicode_string


# print(unicode_char("ṭ"))
