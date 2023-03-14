# Digital Pāḷi Database

## Install

This script converts from the old .ods layout into sqlite db, and then starts building tables of derived data.

1. Download the dpd and roots csvs
2. Download this repo
3. Adjust the paths [here](https://github.com/digitalpalidictionary/dpd-db/blob/3af6916069dd948adc2e6340cd86ca7c7c769bd0/scripts/dpd_db_from_csv.py#L187)
4. Download Tipitaka-Pali-Projector and place it in the `resources` folder.
5. `poetry install`, `poetry shell`
6. bash scripts/makedb.sh

## Info
`PaliWord` and `PaliRoots` tables are the heart of the db, everything else gets derived from those.
They have a relationship `PaliWord.paliroot` `.root` `.root_meaning` etc. to access any root information
There are also lots of `@properties` in the model to create useful derived information.  

`DerivedData` is lists of inflections in multiple languages and the html inflection tables.
`FamilyCompound` is html tables of all the compound words which contain a specific word
`FamilyRoot` is html table of all the words with the same prefix and root
`FamilySet` is html tables of all the words which belong to the same set, e.g. names of monks
`FamilyWord` is html tables of all the words which are derived from a word without a root
`InflectionTemplates` are the templates from which all the inflection tables are derived
`Sandhi` is all the sandhi compound which have been split by code.

## Structure of the code

There are four parts to the code:

1. Create the database and build up the derived data.
2. Add new words, edit and update the db with a GUI. 
3. Run data integrity tests on the db.
4. Compile all the parts and export into dictionary formats like GoldenDict and MDict.  
