import pickle
from rich import print


def make_word_count_dict():
    """Count the length of words to find the problem cases."""

    with open("db/deconstructor/assets/unmatched_set", "rb") as f:
        unmatched_set = pickle.load(f)

    wc_dict = {}
    for word in unmatched_set:
        length = len(word)
        if length not in wc_dict:
            wc_dict[length] = [word]
        else:
            wc_dict[length] += [word]

    key_list = sorted(wc_dict.keys(), reverse=True)
    # print(key_list)

    for key in key_list:
        if key > 100:
            print(key, wc_dict[key])

    for k, v in wc_dict.items():
        if k > 100:
            print(k, v)


make_word_count_dict()
