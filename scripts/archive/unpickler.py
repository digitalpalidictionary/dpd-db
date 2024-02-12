import pickle

with open("temp/limited_data_list", "rb") as f:
    data_list = pickle.load(f)

for c, i in enumerate(data_list):
    print(f"{c:<10}{i['word']}")
