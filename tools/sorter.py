from typing import List

pali_alphabet_string: str = "√aāiīuūeokkhgghṅcchjjhñṭṭhḍḍḥṇtthddhnpphbbhmyrlsvhḷṃ1234567890"

pali_alphabet_list = [
    " ", "√", "a", "ā", "i", "ī", "u", "ū", "e", "o",
    "k", "kh", "g", "gh", "ṅ",
    "c", "ch", "j", "jh", "ñ",
    "ṭ", "ṭh", "ḍ", "ḍḥ", "ṇ",
    "t", "th", "d", "dh", "n",
    "p", "ph", "b", "bh", "m",
    "y", "r", "l", "s", "v", "h", "ḷ", "ṃ",
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"
]


def sort_key(word):
    # comp iteration condition
    dl = [i for i in pali_alphabet_list if len(i) > 1]

    for i in dl:
        word = word.replace(i, '/{}'.format(i))

    wordVe = []

    k = -3

    for j in range(len(word)):
        if word[j] == '/':
            k = j
            wordVe.append(word[j + 1:j + 3])
        if j > k + 2:
            wordVe.append(word[j])

    word = wordVe

    pāli_alphabet_string = '-'.join(pali_alphabet_list)
    return [pāli_alphabet_string.find('-' + x + '-') for x in wordVe]

# key=lambda x: x.map(sort_key)


def pali_list_sorter(list: List):
    pali_alphabet = "√aāiīuūeokgṅcjñṭḍṇtdnpbmyrlsvhḷṃ1234567890 "
    list = sorted(
        list, key=lambda x: [pali_alphabet.index(c) for c in x])
    return list
