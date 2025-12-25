import re
from pathlib import Path

def extract_variables(text, pattern):
    return set(re.findall(pattern, text))

def main():
    webapp_path = Path("exporter/webapp/templates/dpd_headword.html")
    goldendict_path = Path("exporter/goldendict/templates/dpd_sutta_info.html")

    if not webapp_path.exists() or not goldendict_path.exists():
        print("Error: One or both template files not found.")
        return

    webapp_content = webapp_path.read_text(encoding="utf-8")
    goldendict_content = goldendict_path.read_text(encoding="utf-8")

    # Extract Sutta Info section from Webapp (it's inside {% if d.i.needs_sutta_info_button %})
    # This is a rough extraction to focus on the relevant part
    start_marker = '{% if d.i.needs_sutta_info_button %}'
    end_marker = '{% endif %}'
    
    # We'll just search the whole file for d.su variables as they differ from d.i variables
    
    webapp_vars = extract_variables(webapp_content, r"d\.su\[(\\w+)\]")
    goldendict_vars = extract_variables(goldendict_content, r"su\[(\\w+)\]")

    print(f"Webapp Sutta Vars (Count: {len(webapp_vars)})")
    print(f"GoldenDict Sutta Vars (Count: {len(goldendict_vars)})")

    missing_in_goldendict = webapp_vars - goldendict_vars
    extra_in_goldendict = goldendict_vars - webapp_vars

    print("\n--- Missing in GoldenDict (To Add) ---")
    for var in sorted(missing_in_goldendict):
        print(var)

    print("\n--- Extra in GoldenDict (To Check) ---")
    for var in sorted(extra_in_goldendict):
        print(var)

if __name__ == "__main__":
    main()
