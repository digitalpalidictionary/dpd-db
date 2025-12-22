# DPD Audio Database

### Create .mp3 files
Uses the Bhashini API to generate audio Pāḷi pronunciation mp3's. 
```bash
uv run python audio/bhashini/bhashini_generate.py
```

### Create SQLite database
Store the .mp3 pronunciation files as binary blobs in an SQLite database. 
```bash
uv run python audio/bhashini/bhashini_generate.py
```

### Upload New Database
Since the database file is too large to commit to GitHub, it is distributed via a GitHub release instead.
```bash
uv run python audio/db_release_upload.py
```

### Download Latest Database
Download the latest GitHub database release and update the local database.
```bash
uv run python audio/db_release_download.py
```

