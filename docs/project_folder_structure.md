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
├── docs  
├── dps  
├── exporter  
│   ├── bold_definitions  
│   ├── deconstructor  
│   ├── ebook  
│   ├── goldendict  
│   ├── grammar_dict  
│   ├── kobo  
│   ├── other_dictionaries  
│   ├── share  
│   ├── sinhala  
│   ├── tbw  
│   ├── tpr  
│   └── webapp  
├── gui  
├── resources  
├── scripts  
│   ├── archive  
│   ├── bash  
├── shared_data  
├── temp  
├── tests  
└── tools  

## Folder details

- **db/** All code related to building and populating the various tables and columns of the database.

    - **models.py** SQLAlchemy model of the database.
    
    - **db_helpers.py** Helper functions to make create the database, get a session, get column names, etc. 
    
    - **backup_tsv/** TSV backups of the database source tables
    
    - **bold_definitions/** Extract bold definitions from CST texts and compile for easy searching.
    
    - **deconstructor/** A lot of code to break up compounds words

	- **db/epd/** Compile data for the English to Pāḷi dictionary.

	- **families/** Compile HTML and JSON lists to populate the `family_compound`, `family_idiom`, `family_root`, `family_word` and `family_set` tables in the database, for easy access. 

	- **frequency/** Create the frequency maps for every word in CST texts.

	- **inflections/** Populate the `inflection_templates` table and use that to create HTML inflection tables for every word.

	- **lookup/** Populate the `lookup` table for instant accces to every word in the dictionary. 

	- **sanskrit/** Data used for updating the `sanskrit` column in the `dpd_headwords` table.

	- **sinhala/** Data used to populate the `sinhala` table.

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

- **gui/** A GUI for data capture and running database tests

- **resources/** All external resources used by the project, imported as submodules

- **scripts/** Useful scripts for project maintenance.

	- **scripts/archive/** Once useful scripts now languishing in obscurity.

	- **scripts/bash/** Bash scripts used for building the database and exporting.

- **shared_data/** Mostly pickle files used across the project.

- **tests/** Tests to ensure the completeness and accuracy of the database.

- **tools/** Python modules used across the project.

<!-- Link to Subhuti's website -->