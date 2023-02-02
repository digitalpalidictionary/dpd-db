import pandas as pd

df_old = pd.read_csv("../csvs/dpd-full.csv", sep="\t")
df_old = df_old.fillna("")
df_old = df_old.sort_values(by=["Pāli1"])
print(len(df_old))

df_new = pd.read_csv("csvs/dpd-full.csv", sep="\t")
df_new = df_new.fillna("")
df_new = df_new.sort_values(by=["Pāli1"])
print(len(df_new))

for row in range(len(df_old)):
	row_old = df_old.iloc[row]
	row_new = df_new.iloc[row]
	exceptions = [3]
	for i in range(len(row_old)):
		if row_old[i] == row_new[i]:
			print(f"{i} {row_old[i]} == {row_new[i]}")
		else:
			if i not in exceptions:
				print(f"{i} {row_old[i]} != {row_new[i]}")
				input()
			else:
				print(f"{i} {row_old[i]} == {row_new[i]}")

		