import re


def write_to_tsv(output_path, headword, pos, meaning):
    """Write a processed entry to the TSV file."""
    headword_out = headword
    # Apply headword normalization based on POS (inherited logic)
    if re.search(r"in$", headword.lower()) and pos == "masc":
        headword_out = headword[:-2] + "ī"
    elif re.search(r"an$", headword.lower()) and pos == "masc":
        headword_out = headword[:-2] + "a"

    headword_out = headword_out.replace("ṁ", "ṃ")

    with open(output_path, "a") as f:
        f.write(f"{headword_out}\t{pos}\t{meaning}\n")

    return headword_out


def write_no_source(output_path, word):
    with open(output_path, "a") as f:
        f.write(f"{word}\t\t\n")
