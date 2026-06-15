# -*- coding: utf-8 -*-
import csv

csv1 = "../../csvs/dpd-full.csv"
csv2 = "../csvs/dpd-full.csv"

# csv1 = ("../../csvs/roots.csv")
# csv2 = ("../csvs/roots.csv")

with open(csv1, "r") as file:
    reader1 = csv.reader(file)
    data1 = list(reader1)


with open(csv2, "r") as file:
    reader2 = csv.reader(file)
    data2 = list(reader2)


for i1 in range(4, len(data1)):
    d1 = data1[i1][0].split("\t")
    d2 = data2[i1][0].split("\t")
    for i2 in range(len(d1)):
        print(d1[i2], d2[i2])
        if d1[i2] != d2[i2]:
            if d1[i2] == "√":
                continue
            else:
                input()
