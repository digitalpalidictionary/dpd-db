# Digital Pāḷi Database

## Building the DB
1. Download this repo
2. Get [tipitaka-xml](https://github.com/VipassanaTech/tipitaka-xml) with `git
   submodule init && git submodule update` commands
3. Install [nodejs](https://nodejs.org/en/download) 
4. Install [poetry](https://python-poetry.org/docs/)
5. `poetry install`
6. `poetry run bash bash/initial_setup_run_once.sh`
7. `poetry run bash bash/build_db.sh`
8. To be able to run database tests you may need to install some of [these packages.](https://pyperclip.readthedocs.io/en/latest/index.html#not-implemented-error)

That should create an SQLite database `./dpd.db` which can be accessed by [DB Browser](https://sqlitebrowser.org/),  [DBeaver](https://dbeaver.io/), through [SQLAlechmy](https://www.sqlalchemy.org/) or your preferred method. 

For a quick tutorial on how to access any information in the db with SQLAlchemy, see `scripts/db_search_example.py`.

## Repo structure

- [`db`](db/) — database models and related
- [`exporter`](exporter/) — scripts to make output assets
- [`gui`](gui/) — database editing graphical toolkit
- [`tools`](tools/) — Python helper modules to be imported

## Code Structure
There are four parts to the code:
1. Create the database and build up the tables of derived data.
2. Add new words, edit and update the db with a GUI. 
3. Run data integrity tests on the db.
4. Compile all the parts and export into various dictionary formats.

## About the database
- `PaliWord` and `PaliRoots` tables are the heart of the db, everything else gets derived from those.  
- They have a relationship `PaliWord.rt.` to access any root information. For example, `PaliWord.rt.root_meaning`
- There are also lots of `@properties` in `db/models.py` to access useful derived information.  
- `DerivedData` table is lists of inflections of every word in multiple scripts, as well as html inflection tables.
- `FamilyCompound` table is html of all the compound words which contain a specific word.  
- `FamilyRoot` table is html of all the words with the same prefix and root.  
- `FamilySet` table is html of all the words which belong to the same set, e.g. names of monks.  
- `FamilyWord` table is html of all the words which are derived from a common word without a root.  
- `InflectionTemplates` table are the templates from which all the inflection tables are derived.  
- `Sandhi` table is all the deconstructed compounds which have been split by code.  
