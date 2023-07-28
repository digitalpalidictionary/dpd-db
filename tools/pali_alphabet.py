"""Various lists related to the Pāḷi alphabet and its subdivisions."""

pali_alphabet = [
    "a", "ā", "i", "ī", "u", "ū", "e", "o",
    "k", "kh", "g", "gh", "ṅ",
    "c", "ch", "j", "jh", "ñ",
    "ṭ", "ṭh", "ḍ", "ḍh", "ṇ",
    "t", "th", "d", "dh", "n",
    "p", "ph", "b", "bh", "m",
    "y", "r", "l", "s", "v", "h", "ḷ", "ṃ"
    ]


vowels = [
    "a", "ā", "i", "ī", "u", "ū", "e", "o"
    ]

consonants = [
    "k", "kh", "g", "gh", "ṅ",
    "c", "ch", "j", "jh", "ñ",
    "ṭ", "ṭh", "ḍ", "ḍh", "ṇ",
    "t", "th", "d", "dh", "n",
    "p", "ph", "b", "bh", "m",
    "y", "r", "l", "s", "v", "h", "ḷ", "ṃ"
    ]

unaspirated = [
    "k", "g",
    "c", "j",
    "ṭ", "ḍ",
    "t", "d",
    "p", "b",

]
aspirated = [
    "kh", "gh",
    "ch", "jh",
    "ṭh", "ḍh",
    "th", "dh",
    "ph", "bh"
]

nasals = [
    "ṅ",
    "ñ",
    "ṇ",
    "n",
    "m",
    "ṃ"
]

gutterals = [
    "k", "kh", "g", "gh", "ṅ"
    ]

palatals = [
    "c", "ch", "j", "jh", "ñ"
    ]

retroflexes = [
    "ṭ", "ṭh", "ḍ", "ḍh", "ṇ"
    ]

dentals = [
    "t", "th", "d", "dh", "n"
    ]

labials = [
    "p", "ph", "b", "bh", "m"
    ]

semi_vowels = [
    "y", "r", "l", "s", "v", "h", "ḷ"
    ]

niggahita = [
    "ṃ"
    ]

alphabet = (
    vowels +
    gutterals + palatals + retroflexes + dentals + labials +
    semi_vowels + niggahita)
