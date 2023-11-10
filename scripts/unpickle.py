"""A Pickle file reader."""

import pickle
from rich import print

filepath = "gui/additions"
with open(filepath, "rb") as file:
    listy = pickle.load(file)
    for i in listy:
        dict = vars(i[0])
        for k, v in dict.items():
            if v:
                print(f"{k:<20}:{v}")
        print("-"*50)
        
        
print(len(listy))

