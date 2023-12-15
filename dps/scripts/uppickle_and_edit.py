"""A Pickle file reader and editor."""

import pickle
from tools.paths import ProjectPaths

pth = ProjectPaths()

def load_pickled_data(filepath):
    """Load data from a pickled file."""
    with open(filepath, "rb") as file:
        data = pickle.load(file)
    return data

def print_values(data):
    """Print the values in the loaded data."""
    print(data)

def print_values_with_row_numbers(data):
    """Print the values in the loaded data along with their row numbers."""
    for index, item in enumerate(data, start=0):
        print(f"Row {index}: {item}")

def remove_row(data, index_to_remove):
    """Remove a specific row from the data."""
    if 0 <= index_to_remove < len(data):
        removed_row = data.pop(index_to_remove)
        print("Removed row:", removed_row)
        return True
    else:
        print("Invalid index to remove")
        return False

def save_modified_data(data, filepath):
    """Save the modified data back to the pickled file."""
    with open(filepath, "wb") as file:
        pickle.dump(data, file)

# usage
filepath = pth.additions_pickle_path

# additions_pickle_path
# daily_record_path

data = load_pickled_data(filepath)
# print_values(data)
print_values_with_row_numbers(data)

# index_to_remove = 9  # Replace this with the actual index you want to remove
# if remove_row(data, index_to_remove):
#     save_modified_data(data, filepath)
