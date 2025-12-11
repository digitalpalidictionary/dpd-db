import re


def clean_string(text: str) -> str:
    """Clean string by removing brackets, curly braces, trailing fullstops, and footnote markers."""
    cleaned = text.replace("[", "").replace("]", "")  # Remove brackets
    cleaned = cleaned.replace("(", "").replace(")", "")  # Remove brackets
    cleaned = re.sub(r"\{[^}]*\}", "", cleaned)  # Remove {.*} patterns
    cleaned = cleaned.rstrip(".")  # Remove trailing fullstops
    return cleaned.strip()
