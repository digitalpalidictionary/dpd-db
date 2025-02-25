import csv
import re

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', str(s[0]))]  # Extract first value

# Read and validate CSV
with open('dps/csvs/temp.csv', 'r') as f:
    reader = csv.reader(f)
    rows = list(reader)

# Sort rows using natural order
sorted_rows = sorted(rows, key=natural_sort_key)

# Write sorted CSV
with open('dps/csvs/temp.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(sorted_rows)