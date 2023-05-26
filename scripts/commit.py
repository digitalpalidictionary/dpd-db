from git import Repo
from git import Actor
from datetime import datetime

today = datetime.today()
date = datetime.date(today)

repo = Repo("backup_tsv/")
index = repo.index
index.add(["PaliRoot.tsv", "PaliWord.tsv"])
author = Actor("bdhrs", "bodhirasa@gmail.com")
# index.commit(f"update {date}", author=author)
index.commit(f"update {date}")
