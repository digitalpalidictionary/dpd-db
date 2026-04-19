#!/usr/bin/env python3

import re


def clean_sc_sutta(s: str) -> str:
    s = s.strip()
    if not s:
        return ""
    s = s.replace("ṁ", "ṃ")
    s = re.sub(r"^\d+[\.\s]\s*", "", s)
    s = re.sub(r"[\(\[].*?[\)\]]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return ""
    if s.endswith("ṃ"):
        s = s[:-1]
    return s.lower()


def clean_bjt_sutta(s: str) -> str:
    s = s.strip()
    if not s:
        return ""
    s = re.sub(r"^\d+\.\s*", "", s)
    if s.endswith("ṃ"):
        s = s[:-1]
    return s.lower()
