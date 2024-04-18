"""A Pickle file reader."""

import pickle
from rich import print

filepath = "temp/limited_data_list"
with open(filepath, "rb") as file:
    listy = pickle.load(file)

    # for i in listy:
    #     print(i)
    with open("temp/limited_data.txt", "w") as f:
        f.write(str(listy[:10]))
        
print(len(listy))

