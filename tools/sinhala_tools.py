"""Sinhala translation and transliteration helpers: Pāḷi roman ↔ Sinhala
script via aksharamukha, plus Sinhala renderings of POS terms.
Used by db inflections/lookup transliteration and BJT processing."""

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
    text_translit: str = transliterate.process(
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
