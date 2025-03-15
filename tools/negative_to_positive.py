from db.models import DpdHeadword
import re


def make_positive(i: DpdHeadword):
    """Logically creates a positive version of a negative Pāḷi word."""

    positive = ""
    if len(i.lemma_clean) > 2:
        if i.lemma_clean.startswith("na"):
            if i.lemma_clean[2] == i.lemma_clean[3]:
                positive = i.lemma_clean[3:]
            else:
                positive = i.lemma_clean[2:]

        elif i.lemma_clean.startswith("an"):
            if re.sub("^na > an + ", "", i.construction).startswith("n"):
                positive = i.lemma_clean[2:]
            else:
                positive = i.lemma_clean[2:]

        elif i.lemma_clean.startswith("nā"):
            positive = f"a{i.lemma_clean[2:]}"

        elif i.lemma_clean.startswith("a"):
            if i.lemma_clean[1] == i.lemma_clean[2]:
                positive = i.lemma_clean[2:]
            elif re.sub("^a + ", "", i.construction).startswith("n"):
                positive = i.lemma_clean[1:]
            else:
                positive = i.lemma_clean[1:]
        elif i.lemma_clean.startswith("ni"):
            positive = i.lemma_clean[3:]
        elif i.lemma_clean.startswith("nu"):
            positive = i.lemma_clean[1:]
        elif i.lemma_clean.startswith("nū"):
            positive = f"u{i.lemma_clean[2:]}"
        elif i.lemma_clean.startswith("ne"):
            positive = i.lemma_clean[1:]
        elif i.lemma_clean.startswith("no"):
            if i.lemma_clean[2] == "p":
                positive = f"u{i.lemma_clean[2:]}"
            else:
                positive = i.lemma_clean[1:]

    return positive
