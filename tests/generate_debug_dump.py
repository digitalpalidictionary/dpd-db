import json
from exporter.mcp.analyzer import analyze_sentence
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths


def generate_dump():
    pth = ProjectPaths()
    session = get_db_session(pth.dpd_db_path)

    sentences = [
        "buddho dhammena desetvā",
        "yo'dha",
        "dhammacakkappavattana",
        "dve'me bhikkhave antā pabbajitena na sevitabbā",
    ]

    full_output = {}

    for sentence in sentences:
        print(f"Analyzing: {sentence}")
        result = analyze_sentence(sentence, session)
        full_output[sentence] = result

    output_path = "temp/debug_analysis_dump.json"
    with open(output_path, "w") as f:
        json.dump(full_output, f, indent=2, ensure_ascii=False)

    print(f"Dump saved to {output_path}")
    session.close()


if __name__ == "__main__":
    generate_dump()
