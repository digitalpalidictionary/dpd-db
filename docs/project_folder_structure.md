# Project folder structure
Where are all the parts of the project located?

## Tree
.  
├── db  
│   ├── backup_tsv  
│   ├── bold_definitions  
│   ├── deconstructor  
│   ├── epd  
│   ├── families  
│   ├── frequency  
│   ├── inflections  
│   ├── lookup  
│   ├── sanskrit  
│   └── sinhala  
├── db_tests  
├── docs  
├── dps  
├── exporter  
│   ├── bold_definitions  
│   ├── deconstructor  
│   ├── goldendict  
│   ├── grammar_dict  
│   ├── kindle
│   ├── kobo  
│   ├── other_dictionaries  
│   ├── share  
│   ├── sinhala  
│   ├── tbw  
│   ├── tpr  
│   └── webapp  
├── go_modules  
│   ├── deconstructor  
│   ├── dpdDb  
│   ├── frequency  
│   ├── tools  
├── gui  
├── resources  
├── scripts  
│   ├── add  
│   ├── archive  
│   ├── backup  
│   ├── bash  
│   ├── build  
│   ├── export  
│   ├── find  
│   ├── fix  
│   ├── info  
│   ├── tutorial  
├── shared_data  
├── temp  
└── tools  

## Code Structure

There are four main parts to the code:

1. __db__: Create the database and build up the tables of derived data.
2. __db_tests__: Run data integrity tests on the db.
3. __gui__: Add new words, edit and update the db with a GUI.  
4. __exporter__: Compile all the parts and export into various dictionary formats.

## Folder details

- **db/** All code related to building and populating the various tables and columns of the database.

    - **models.py** SQLAlchemy model of the database.
    
    - **db_helpers.py** Helper functions to make create the database, get a session, get column names, etc. 
    
    - **backup_tsv/** TSV backups of the database source tables
    
    - **bold_definitions/** Extract bold definitions from CST texts and compile for easy searching.

	- **db/epd/** Compile data for the English to Pāḷi dictionary.

	- **families/** Compile HTML and JSON lists to populate the `family_compound`, `family_idiom`, `family_root`, `family_word` and `family_set` tables in the database, for easy access. 

	- **frequency/** Create the frequency maps for every word in CST texts.

	- **inflections/** Populate the `inflection_templates` table and use that to create HTML inflection tables for every word.

	- **lookup/** Populate the `lookup` table for instant accces to every word in the dictionary. 

	- **sanskrit/** Data used for updating the `sanskrit` column in the `dpd_headwords` table.

	- **sinhala/** Data used to populate the `sinhala` table.

- **db_tests/** Tests to ensure the completeness and accuracy of the Pāḷi database.

- **docs/** Helpful project documentation.

	- **project_folder_structure.md** What you're reading right now.

	- **dpd_headwords_table.md** Description of the real and virtual columns in the `dpd_headwords` table.

- **dps/** All Devamitta's code related to creating and populating `russian` and `sbs` tables

- **exporter/** Export the DPD database into various formats.

	- **deconstructor/** Export DPD Deconstructor to GoldenDict and MDict

	- **goldendict/** Export DPD, EPD, Help and Abbreviations to GoldenDict and MDict

	- **grammar_dict/** Export DPD Grammar to GoldenDict and MDict

	- **kindle/** Export a light version of DPD for Kindle.

	- **kobo/** Export a light version of DPD for Kobo eReader.

	- **other_dictionaries/** Export other Pāḷi and Sanskrit dictionaries to GoldenDict and MDict

	- **sinhala/** Export a light version of DPD in Sinhala to GoldenDict and MDict

	- **tbw/** Export a light version of DPD for integration into [The Buddha's Words website](https://thebuddhaswords.net/mn/mn1.html).

	- **tpr/** Export DPD grammar deconstructor data for integration into Tipitaka Pali Reader app 

	- **webapp/** A web application using the DPD database and FastApi, hosted at [www.dpdict.net](www.dpdict.net)

- **go_modules/** When Python is too slow, write it in GO

	- **deconstructor/** Breaking up a more than a million compound words

	- **dpdDb/** Access the database using GORM

	- **frequency/** Generate frequency tables and data lists for every word

	- **tools/** GO packages used across the project

- **gui/** A GUI for data capture and running database tests

- **resources/** All external resources used by the project, imported as submodules

- **scripts/** Useful scripts for project maintenance.

	see [scripts readme](scripts/README.md) for more info.

- **shared_data/** Data used across the project.

- **tools/** Python modules used across the project.

<!-- Link to Subhuti's website -->