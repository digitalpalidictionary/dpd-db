import pandas as pd
from rich import print
from tools.paths import ProjectPaths

pth = ProjectPaths()
matches = pd.read_csv(pth.matches_path, sep="\t")
matches_do = pd.read_csv(pth.matches_do_path, sep="\t")
matches_do_old = pd.read_csv("db/deconstructor/output_do_old/matches.tsv", sep="\t")
print("[green]matches_do")
print(matches_do)

missing_words = matches_do_old[~matches_do_old["word"].isin(matches_do["word"])]
print("[green]missing_words")
print(missing_words)
missing_words.to_csv(
    "db/deconstructor/output_do/missing_words.tsv", sep="\t", index=False
)

matches_do = pd.concat([matches_do, missing_words])
print("[green]matches_do + missing_words")
print(matches_do)

# matches_do = pd.concat([matches_do, matches])
# print("[green]matches + missing_words + matches")
# print(matches_do)

matches_do.to_csv(pth.matches_do_path, sep="\t", index=False)
