import pandas as pd
from tools.paths import ProjectPaths

pth = ProjectPaths()
df = pd.read_csv(pth.matches_sorted, sep="\t")
pd.options.display.max_rows = 100
top_100 = df["word"].value_counts().head(100)

print(top_100)
