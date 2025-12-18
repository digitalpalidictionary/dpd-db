from aksharamukha import transliterate

pos_dict = {
    "letter": {"pos_si": "අ", "pos_si_full": "අකුර"},
    "prefix": {"pos_si": "උප", "pos_si_full": "උපසර්ග"},
    "cs": {"pos_si": "විප්‍ර", "pos_si_full": "විකරණ ප්‍රත්‍යය"},
    "abbrev": {"pos_si": "කෙටියෙ", "pos_si_full": "කෙටි යෙදුම්"},
    "adj": {"pos_si": "විශේ", "pos_si_full": "විශෙෂණ පද"},
    "pron": {"pos_si": "සර්", "pos_si_full": "සර්වනාම"},
    "ptp": {"pos_si": "කි", "pos_si_full": "කිතක/කිච්ච ප්‍රත්‍යය"},
    "pp": {"pos_si": "අකෘ", "pos_si_full": "අතීත කෘදන්ත"},
    "masc": {"pos_si": "පු", "pos_si_full": "පුල්ලිංග"},
    "aor": {"pos_si": "අතී", "pos_si_full": "අජ්ජතනී, අතීත කාළ"},
    "nt": {"pos_si": "න", "pos_si_full": "නපුංසක ලිංග"},
    "fem": {"pos_si": "ඉ", "pos_si_full": "ඉත්ථි ලිංග"},
    "ind": {"pos_si": "නි", "pos_si_full": "නිපාත. අව්‍ය පද"},
    "prp": {"pos_si": "මික්‍රි", "pos_si_full": "මිශ්‍ර ක්‍රියා"},
    "abs": {"pos_si": "පූ", "pos_si_full": "පූර්ව ක්‍රියා"},
    "cond": {"pos_si": "කා", "pos_si_full": "කාලාතිපත්ති,සත්තමී"},
    "imperf": {"pos_si": "අකා", "pos_si_full": "අතීත කාළ/හීයත්තනී"},
    "sandhi": {"pos_si": "සන්ධි", "pos_si_full": "සන්ධි"},
    "idiom": {"pos_si": "භා", "pos_si_full": "භාෂා රීතියට අනුගත පද"},
    "pr": {"pos_si": "වකා", "pos_si_full": "වර්තමාන කාළ"},
    "inf": {"pos_si": "අව්‍ය", "pos_si_full": "තුමන්ත,අව්‍ය"},
    "ger": {"pos_si": "භාව", "pos_si_full": "අව්‍යය, භාව පද"},
    "card": {"pos_si": "සං", "pos_si_full": "සංඛ්‍යා ශබ්ද"},
    "ordin": {"pos_si": "සං.පූ", "pos_si_full": "සංඛ්‍යා පූරණ ශබ්ද"},
    "imp": {"pos_si": "වික්‍රි", "pos_si_full": "පඤ්චමී/විධි ක්‍රියා"},
    "opt": {"pos_si": "සත්", "pos_si_full": "ඉච්ඡිතාර්ථය,සත්තමී"},
    "ve": {"pos_si": "වාච්‍ය", "pos_si_full": "වාච්‍ය"},
    "root": {"pos_si": "ධාතුව", "pos_si_full": "ධාතුව"},
    "suffix": {"pos_si": "ප්‍රත්‍ය", "pos_si_full": "ප්‍රත්‍ය"},
    "perf": {"pos_si": "පරො", "pos_si_full": "පරොක්ඛා "},
    "fut": {"pos_si": "අකා", "pos_si_full": "අනාගත කාළ"},
}


def pos_si(pos: str):
    return pos_dict[pos]["pos_si"]


def pos_si_full(pos: str):
    return pos_dict[pos]["pos_si_full"]


def translit_ro_to_si(text: str) -> str:
    return transliterate.process(
        "IASTPali",
        "Sinhala",
        text,
        post_options=["SinhalaPali", "SinhalaConjuncts"],
    )  # type:ignore


def translit_si_to_ro(text: str) -> str:
    text_translit = transliterate.process(
        "Sinhala",
        "IASTPali",
        text,
        post_options=["SinhalaPali", "SinhalaConjuncts"],
    )  # type:ignore

    text_translit = (
        text_translit.replace("ï", "i")
        .replace("ü", "u")
        .replace("ĕ", "e")
        .replace("ŏ", "o")
    )

    return text_translit


gram_dict = {
    "nom": "පඨමා",
    "acc": "දුතියා",
    "instr": "තතියා",
    "dat": "චතුත්ථී",
    "abl": "පඤ්චමී",
    "gen": "ඡට්ඨි",
    "loc": "සත්තමී",
    "voc": "ආලපන",
    "In comps": "සන්ධිවල",
    "fem sg": "ඉ ඒක",
    "fem pl": "ඉ බහු",
    "masc sg": "පු ඒක",
    "masc pl": "පු බහු",
    "neut sg": "න ඒක",
    "neut pl": "න බහු",
    "declension, conjugation": "වරනැගීම",
    "sg": "ඒක",
    "pl ": "බහු",
    "reflexive sg": "අත්තනො ඒක",
    "reflexive pl": "අත්තනො බහු",
    "pr  3rd": "වත් පඨ",
    "pr 2nd": "වත් මජ්",
    "pr 1st": "වත් උත්",
    "imp 3rd": "පඤ් පඨ",
    "imp 2nd": "පඤ් මජ්",
    "imp 1st": "පඤ් උත්",
    "opt 3rd": "සත් පඨ",
    "opt 2nd": "සත් මජ්",
    "opt 1st": "සත් උත්",
    "fut 3rd": "භවි පඨ",
    "fut 2nd": "භවි මජ්",
    "fut 1st": "භවි උත්",
    "aor 3rd": "අජ් පඨ",
    "aor 2nd": "අජ් මජ්",
    "aor 1st": "අජ් උත්",
    "pref 3rd": "පරො පඨ",
    "pref 2nd": "පරො මජ්",
    "pref 1st": "පරො උත්",
    "cond 3rd": "කාලාති පඨ",
    "cond 2nd": "කාලාති මජ්",
    "cond 1st": "කාලාති උත්",
    "Imperf 3rd": "හීය පඨ",
    "Imperf 2nd": "හීය මජ්",
    "Imperf 1st": "හීය උත්",
    "1st sg": "උත් ඒක ",
    "1st pl": "උත් බහු",
    "pron": "සර්",
    "subject": "කර්තෘ",
    "object": "කර්මය",
    "2nd sg": "මජ් ඒක",
    "2nd pl": "මජ් බහු",
    "3rd sg": "පඨ ඒක ",
    "3rd pl": "පඨ බහු",
    "Inflections not found in the Chaṭṭha Saṅgāyana corpus, or within processed sandhi compounds are grayed out. They might still occur elsewhere, within compounds or in other versions of the Pāḷi texts.": " ඡට්ඨ සංගායනා ත්‍රිපිටකයෙහි පද හෝ සන්ධි පද තුළ දක්නට නොලැබෙන  පද අළු පැහැයෙන් යුක්ත වේ. ඒවා  වෙනත්  පොත්වල හෝ සන්ධි තුළ හෝ වෙනත් ත්‍රිපිටක අනුවාදවල තිබිය හැක.",
    "Did you spot a mistake in the declension table? Something missing? Report it here.": "වරනැගීම් වගුවේ වැරැද්දක් ඔබ දුටුවාද? යමක් අඩු වී තිබේද? එය මෙතනින් වාර්තා කරන්න.",
    "Abbreviation": "කෙටි යෙදුම",
    "Meaning": "තේරුම",
    "Pāḷi": "පාලි",
    "Example": "උදාහරණ",
    "Information": "තොරතුරු",
    "Nominative case": "පඨමා විභත්ති",
    "Paṭhamā, paccattavacana": "පඨමා, පච්චත්තවචන",
    "The category of nouns serving as the grammatical subject of a verb": "ක්‍රියා පදයට විෂය වන පදය හෙවත් උක්ත පද කාණ්ඩය",
    "Present tense": "වර්තමාන කාලය",
    "past tense": "අතීත කාලය",
    "future tense": "අනාගත කාලය",
    "A verb tense that expresses actions or states at the time of speaking (e.g. lives; appears; sees)": "මේ මොහොතේදී සිදුවන ක්‍රියාවක් හෝ සිදුවීමක් ප්‍රකාශ කරන ක්‍රියා පදය (උදා: ජීවත්වෙයි; දිස්වේ; දකී)",
    "Aorist verb": "අතීත කාල ක්‍රියාව",
    "A form of a verb that, in the indicative mood, expresses past action. (e.g. was; sat down; arose)": "ක්‍රියා පදයක ආකාරයක්, අතීත ක්‍රියාව ප්‍රකාශ කරයි. (උදා. විය, වාඩිවිය, පැන නැගුණි)",
    "Accusative case": "දුතියා විභත්ති",
    "The object of the sentence (e.g. me)": "වාක්‍යයේ කර්මය (උදා: මම)",
    "Dutiyā, upayogavacana, kammavacana": "දුතියා, උපයොගවචන, කම්මවචන",
}


def si_grammar(text) -> str:
    if text in gram_dict:
        return gram_dict[text]
    else:
        return text
