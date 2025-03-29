
## Building the DB from scratch

-- Download the repo

```shell
git clone --depth=1 https://github.com/digitalpalidictionary/dpd-db.git
```

-- Navigate into the directory

```shell
cd dpd-db
```

-- Download the submodules from Github

```shell
git submodule init && git submodule update
```

-- Install [nodejs](https://nodejs.org/en/download){target="_blank"} for your operating system

-- Install [go](https://go.dev/doc/install){target="_blank"} for your operating system

-- Install [uv](https://astral.sh/uv/install){target="_blank"} for your operating system

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

-- Install all the dependencies with uv
```bash
uv sync
```

-- Having at least 20 GB of RAM can be helpful. If you have less, consider [increasing the swap memory.](https://www.reddit.com/r/linuxmint/comments/uhjyir/how_to_increase_swap_size/?rdt=34113){target="_blank"}.

-- Run this once to initialize the project

```shell
uv run bash scripts/bash/initial_setup_run_once.sh
```

-- Build the database, this can take up to an hour the first time.

```shell
uv run bash scripts/bash/initial_build_db.sh
```

That should create an SQLite database `dpd.db` in the root folder which can be accessed with [DB Browser](https://sqlitebrowser.org/){target="_blank"}, [DBeaver](https://dbeaver.io/){target="_blank"}, through [SQLAlechmy](https://www.sqlalchemy.org/){target="_blank"} or your preferred method.

For a quick tutorial on how to access any information in the db with SQLAlchemy, see [Using the db](use_db.md)

---

## Additional configuration

There are some additional dependencies in different parts of the project that may need to be installed depending on your use case.

1. The __GoldenDict__ exporter requires [dictzip](https://linux-packages.com/ubuntu-24-04/package/dictzip){target="_blank"}

2. Running the __GUI__ requires [tkinter](https://www.pythonguis.com/installation/install-tkinter-linux/){target="_blank"}

3. The __database tests__ may require [pyperclip dependencies](https://pyperclip.readthedocs.io/en/latest/index.html#not-implemented-error){target="_blank"}.