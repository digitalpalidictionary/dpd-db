import json
from pathlib import Path
from rich import print

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def get_key(entry):
    return (
        entry.get("file_name"),
        entry.get("nikaya"),
        entry.get("book"),
        entry.get("title"),
        entry.get("subhead"),
        entry.get("bold"),
        entry.get("bold_end"),
        entry.get("commentary")
    )

def compare():
    # Resolve paths relative to the project root
    root = Path(__file__).parents[3]
    old_path = root / "archive/db/bold_definitions/bold_definitions.json"
    new_path = root / "db/bold_definitions/bold_definitions.json"

    if not old_path.exists():
        print(f"[red]Old path not found: {old_path}")
        return
    if not new_path.exists():
        print(f"[red]New path not found: {new_path}")
        return

    print("[cyan]Loading old definitions...")
    old_data = load_json(old_path)
    print("[cyan]Loading new definitions...")
    new_data = load_json(new_path)

    old_keys = {get_key(e) for e in old_data}
    new_keys = {get_key(e) for e in new_data}

    lost = old_keys - new_keys
    gained = new_keys - old_keys

    print("\n[bold]Comparison Results:[/bold]")
    print(f"Old count: {len(old_data)}")
    print(f"New count: {len(new_data)}")
    print(f"Lost:      {len(lost)}")
    print(f"Gained:    {len(gained)}")

    if lost:
        print("\n[red][bold]First 10 Lost Definitions:[/bold]")
        for i, k in enumerate(list(lost)[:10]):
            print(f"{i+1}. {k}")

    if gained:
        print("\n[green][bold]First 10 Gained Definitions:[/bold]")
        for i, k in enumerate(list(gained)[:10]):
            print(f"{i+1}. {k}")

    # Specific check for the "end of sentence" bug fix
    # We expect gained definitions to often have empty bold_n or punctuation at end of paragraph in XML
    
if __name__ == "__main__":
    compare()
