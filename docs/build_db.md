
## Building the DB from scratch
1. Download the repo

```shell
git clone --depth=1 https://github.com/digitalpalidictionary/dpd-db.git
```

2. Navigate into the directory

```shell
cd dpd-db
```

3. Download the submodules from Github

```shell
git submodule init && git submodule update
```

4. Install [nodejs](https://nodejs.org/en/download) for your operating system

5. Install [go](https://go.dev/doc/install) for your operating system

6. Install [poetry](https://python-poetry.org/docs/) for your operating system

7. Install all the dependencies with poetry

```shell
poetry install
```

8. Run this once to initialize the project

```shell
poetry run bash scripts/bash/initial_setup_run_once.sh
```

9. Build the database, this can take up to an hour the first time.

```shell
poetry run bash scripts/bash/build_db.sh
```

That should create an SQLite database `dpd.db` in the root folder which can be accessed with [DB Browser](https://sqlitebrowser.org/), [DBeaver](https://dbeaver.io/), through [SQLAlechmy](https://www.sqlalchemy.org/) or your preferred method.

For a quick tutorial on how to access any information in the db with SQLAlchemy, see [scripts/tutorial/db_search_example.py](scripts/tutorial/db_search_example.py)

---

## Additional configuration

There are some additional dependencies in different parts of the project that may need to be installed depending on your use case.

1. The __GoldenDict__ exporter requires [dictzip](https://linux-packages.com/ubuntu-24-04/package/dictzip)

2. Running the __GUI__ requires [tkinter](https://www.pythonguis.com/installation/install-tkinter-linux/)

3. The __database tests__ may require [pyperclip dependencies](https://pyperclip.readthedocs.io/en/latest/index.html#not-implemented-error).