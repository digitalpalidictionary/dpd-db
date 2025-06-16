# -*- coding: utf-8 -*-
"""Find all gatha1 gathalast errors in a CST text."""


import re
import pyperclip

cst_text = "resources/tipitaka-xml/romn/s0508m.mul.xml"

with open(cst_text, "r", encoding="utf16") as f:
    text = f.read()

errors = re.findall(r"gatha1(?:(?!gathalast)[\s\S])*?hangnum", text)
print(len(errors))

for error in errors:
    if "…" not in error:
        search_text = re.findall("gatha1.+", error)[0]
        pyperclip.copy(search_text)
        print(error)
        print("-"*50)
        input("press any key to continue ")
