import re
from pathlib import Path


def main():
    webapp_path = Path("exporter/webapp/templates/dpd_headword.html")
    goldendict_path = Path("exporter/goldendict/templates/dpd_sutta_info.html")

    webapp_content = webapp_path.read_text(encoding="utf-8")
    goldendict_content = goldendict_path.read_text(encoding="utf-8")

    # Debugging: check if string exists
    if "d.su.cst_code" in webapp_content:
        print("Found 'd.su.cst_code' in Webapp content.")
    else:
        print("Did NOT find 'd.su.cst_code' in Webapp content.")

    # Regex test
    webapp_matches = re.findall(r"d\.su\[\w+\]", webapp_content)
    print(f"Webapp matches: {len(webapp_matches)}")
    print(f"Sample: {webapp_matches[:5]}")

    goldendict_matches = re.findall(r"su\[\w+\]", goldendict_content)
    print(f"GoldenDict matches: {len(goldendict_matches)}")
    print(f"Sample: {goldendict_matches[:5]}")

    webapp_set = set(webapp_matches)
    goldendict_set = set(goldendict_matches)

    print("\n--- Differences ---")
    print(f"In Webapp but not GoldenDict: {sorted(webapp_set - goldendict_set)}")
    print(f"In GoldenDict but not Webapp: {sorted(goldendict_set - webapp_set)}")


if __name__ == "__main__":
    main()
