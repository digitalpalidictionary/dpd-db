import pickle

filepath = "gui/additions"
with open(filepath, "rb") as file:
    x = pickle.load(file)
    for i in x:
        print(x)
