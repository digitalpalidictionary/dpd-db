"""A Pickle file reader."""

import pickle

def unpickle(filepath: str):

    with open(filepath, "rb") as file:
        unpickled = pickle.load(file)
            
    return unpickled


