import json
import csv
import os

def extract_blurbs(json_file_path):
    """Extracts blurbs from a JSON file.

    Args:
        json_file_path (str): Path to the JSON file.

    Returns:
        list: A list of dictionaries, where each dictionary represents a blurb.
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        blurbs = []
        for category, category_data in data.get('en', {}).items():
            if isinstance(category_data, dict):
                for key, value in category_data.items():
                    blurbs.append({'category': category, 'key': key, 'blurb': value})
            elif isinstance(category_data, str):
                blurbs.append({'category': 'grouping', 'key': category, 'blurb': category_data})
        return blurbs
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading or parsing JSON file: {e}")
        return None

def save_to_tsv(data, tsv_file_path):
    """Saves data to a TSV file.

    Args:
        data (list): A list of dictionaries, where each dictionary represents a row.
        tsv_file_path (str): The path to the TSV file.
    """
    try:
        if not data:
            print("No data to save.")
            return

        # Ensure the directory exists
        os.makedirs(os.path.dirname(tsv_file_path), exist_ok=True)

        with open(tsv_file_path, 'w', newline='', encoding='utf-8') as tsvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(tsvfile, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()
            writer.writerows(data)
        print(f"Data saved to {tsv_file_path}")
    except (IOError, OSError) as e:
        print(f"Error writing to TSV file: {e}")

if __name__ == "__main__":
    json_file = 'resources/sc-data/additional-info/blurbs.json'
    tsv_file = 'scripts/suttas/sc/sc_blurb.tsv'
    blurbs = extract_blurbs(json_file)
    save_to_tsv(blurbs, tsv_file)