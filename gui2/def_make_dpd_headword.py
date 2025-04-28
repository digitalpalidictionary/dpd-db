from db.models import DpdHeadword


def make_dpd_headword_from_dict(field_data: dict[str, str]) -> DpdHeadword:
    """Creates a DpdHeadword object from a dictionary of field data."""

    new_word = DpdHeadword()
    for field_name, value in field_data.items():
        if hasattr(new_word, field_name):
            setattr(new_word, field_name, value if value is not None else "")
    return new_word
