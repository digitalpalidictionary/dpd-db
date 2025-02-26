import re

# Define the custom order for prefixes
PREFIX_ORDER = {
    "dn": 0,
    "mn": 1,
    "sn": 2,
    "an": 3,
    "kp": 4,
    "dhp": 5,
    "ud": 6,
    "iti": 7,
    "snp": 8,
    "vv": 9,
    "pv": 10,
    "thag": 11,
    "thig": 12,
    "tha-ap": 13,
    "thi-ap": 14,
    "bv": 15,
    "cp": 16,
    "ja": 17,
    "mnd": 18,
    "cnd": 19,
    "ps": 20,
    "mil": 21,
    "ne": 22,
    "pe": 23,
}  


def extract_prefix(s, possible_prefixes):
    """
    Extract the prefix from the string based on a list of possible prefixes.
    """
    for prefix in sorted(
        possible_prefixes, key=len, reverse=True
    ):  # Check longer prefixes first
        if s.lower().startswith(prefix):
            return prefix
    return None  # No matching prefix found


def natural_sort_key(s):
    """
    Generate a key for natural sorting of alphanumeric strings with custom prefix order.
    """
    # Extract the prefix dynamically
    prefix = extract_prefix(s, PREFIX_ORDER.keys())

    # Get the priority of the prefix (default to a high number if not in the custom order)
    prefix_priority = PREFIX_ORDER.get(prefix, 999)

    # Remove the prefix from the string for natural sorting
    remaining_string = s[len(prefix) :] if prefix else s

    # Split the remaining string into parts for natural sorting
    parts = re.split("([0-9]+)", remaining_string)

    # Return a tuple: (prefix_priority, natural_sort_parts)
    return (
        prefix_priority,
        [int(text) if text.isdigit() else text.lower() for text in parts],
    )


def sorted_naturally(data):
    """
    Sort the data list based on the 'code' field using natural sorting with custom prefix order.
    """
    return sorted(data, key=lambda x: natural_sort_key(x["code"]))


if __name__ == "__main__":
    # Example data
    data = [
        {"code": "mn110", "title": "Middle Length Discourses 110"},
        {"code": "mn12", "title": "Middle Length Discourses 12"},
        {"code": "sn12.87", "title": "Connected Discourses 12.87"},
        {"code": "sn12.100", "title": "Connected Discourses 12.100"},
        {"code": "sn12.9", "title": "Connected Discourses 12.9"},
        {"code": "dn1", "title": "Long Discourses 1"},
        {"code": "an3.45", "title": "Numerical Discourses 3.45"},
        {"code": "dn22", "title": "Long Discourses 22"},
        {"code": "an1.1", "title": "Numerical Discourses 1.1"},
        {
            "code": "dna100",
            "title": "DNA Discourses 100",
        },  # Example of a 3-character prefix
        {
            "code": "snb50",
            "title": "SNB Discourses 50",
        },  # Example of a 3-character prefix
    ]

    # Sort the data
    sorted_data = sorted_naturally(data)

    # Print the sorted data
    for item in sorted_data:
        print(item)
