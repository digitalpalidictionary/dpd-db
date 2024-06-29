

pos_dict = {
    "letter": {
        "si_pos": "අ",
        "si_pos_full": "අකුර"
    },
    "prefix": {
        "si_pos": "උප",
        "si_pos_full": "උපසර්ග"
    },
    "cs": {
        "si_pos": "විප්‍ර",
        "si_pos_full": "විකරණ ප්‍රත්‍යය"
    },
    "abbrev": {
        "si_pos": "කෙටියෙ",
        "si_pos_full": "කෙටි යෙදුම්"
    },
    "adj": {
        "si_pos": "විශේ",
        "si_pos_full": "විශෙෂණ පද"
    },
    "pron": {
        "si_pos": "සර්",
        "si_pos_full": "සර්වනාම"
    },
    "ptp": {
        "si_pos": "කි",
        "si_pos_full": "කිතක/කිච්ච ප්‍රත්‍යය"
    },
    "pp": {
        "si_pos": "අකෘ",
        "si_pos_full": "අතීත කෘදන්ත"
    },
    "masc": {
        "si_pos": "පු",
        "si_pos_full": "පුල්ලිංග"
    },
    "aor": {
        "si_pos": "අතී",
        "si_pos_full": "අජ්ජතනී, අතීත කාළ"
    },
    "nt": {
        "si_pos": "න",
        "si_pos_full": "නපුංසක ලිංග"
    },
    "fem": {
        "si_pos": "ඉ",
        "si_pos_full": "ඉත්ථි ලිංග"
    },
    "ind": {
        "si_pos": "නි",
        "si_pos_full": "නිපාත. අව්‍ය පද"
    },
    "prp": {
        "si_pos": "මික්‍රි",
        "si_pos_full": "මිශ්‍ර ක්‍රියා"
    },
    "abs": {
        "si_pos": "පූ",
        "si_pos_full": "පූර්ව ක්‍රියා"
    },
    "cond": {
        "si_pos": "කා",
        "si_pos_full": "කාලාතිපත්ති,සත්තමී"
    },
    "imperf": {
        "si_pos": "අකා",
        "si_pos_full": "අතීත කාළ/හීයත්තනී"
    },
    "sandhi": {
        "si_pos": "සන්ධි",
        "si_pos_full": "සන්ධි"
    },
    "idiom": {
        "si_pos": "භා",
        "si_pos_full": "භාෂා රීතියට අනුගත පද"
    },
    "pr": {
        "si_pos": "වකා",
        "si_pos_full": "වර්තමාන කාළ"
    },
    "inf": {
        "si_pos": "අව්‍ය",
        "si_pos_full": "තුමන්ත,අව්‍ය"
    },
    "ger": {
        "si_pos": "භාව",
        "si_pos_full": "අව්‍යය, භාව පද"
    },
    "card": {
        "si_pos": "සං",
        "si_pos_full": "සංඛ්‍යා ශබ්ද"
    },
    "ordin": {
        "si_pos": "සං.පූ",
        "si_pos_full": "සංඛ්‍යා පූරණ ශබ්ද"
    },
    "imp": {
        "si_pos": "වික්‍රි",
        "si_pos_full": "පඤ්චමී/විධි ක්‍රියා"
    },
    "opt": {
        "si_pos": "සත්",
        "si_pos_full": "ඉච්ඡිතාර්ථය,සත්තමී"
    },
    "ve": {
        "si_pos": "වාච්‍ය",
        "si_pos_full": "වාච්‍ය"
    },
    "root": {
        "si_pos": "ධාතුව",
        "si_pos_full": "ධාතුව"
    },
    "suffix": {
        "si_pos": "ප්‍රත්‍ය",
        "si_pos_full": "ප්‍රත්‍ය"
    },
    "perf": {
        "si_pos": "පරො",
        "si_pos_full": "පරොක්ඛා "
    },
    "fut": {
        "si_pos": "අකා",
        "si_pos_full": "අනාගත කාළ"
    }
}

def pos_to_si_pos(pos):
    return pos_dict[pos]["si_pos"]
    

def pos_to_si_pos_full(pos):
    return pos_dict[pos]["si_pos_full"]
