def pali_sort_key(word):
    pāli_alphabet = [
        " ", "√",
        "a", "ā", "i", "ī", "u", "ū", "e", "o",
        "k", "kh", "g", "gh", "ṅ",
        "c", "ch", "j", "jh", "ñ",
        "ṭ", "ṭh", "ḍ", "ḍh", "ṇ",
        "t", "th", "d", "dh", "n",
        "p", "ph", "b", "bh", "m",
        "y", "r", "l", "v", "s", "h", "ḷ", "ṃ",
        "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."
    ]
    try:
        dl = [i for i in pāli_alphabet if len(i) > 1]
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

        def get_index(char):
            try:
                return pāli_alphabet.index(char)
            except ValueError:
                return -1

        return [get_index(x) for x in word]

    except Exception as e:
        print(e)


"""
sort a query:
results = session.query(Sandhi).all()
sorted_results = sorted(results, key=lambda x: pali_sort_key(x.sandhi))
"""

"""
sort a list:
list = sorted(list, key=pali_sort_key)
"""
