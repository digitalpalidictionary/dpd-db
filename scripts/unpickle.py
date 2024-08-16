"""A Pickle file reader."""

import pickle
from rich import print

filepath = "shared_data/changed_templates"
with open(filepath, "rb") as file:
    unpickled = pickle.load(file)
        
print(unpickled)


