## Using the DB

There is a comprehensive database model and lots of pre-existing tools in the repo. To use them:

1. Clone this repo
2. Download **dpd.db.tar.bz2** from [this page](https://github.com/digitalpalidictionary/dpd-db/releases), 
3. Unzip and place the db in the root of the project folder
4. Install [uv](https://astral.sh/uv/install) for your operating system
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
5. Install all the dependencies with uv
```bash
uv sync
```
6. See [`scripts/tutorial/db_search_example.py`](../scripts/tutorial/db_search_example.py) for a quick tutorial on how to use the database with SQLAlchemy

Alternatively, just download the db and use it with your tools of choice. 
