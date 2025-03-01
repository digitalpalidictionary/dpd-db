#!/bin/bash

# This script builds dpd.db from scratch and export all dictionaries.
# It will take an hour to run for the first time.
# WARNING! This will destroy your existing db.

scripts/bash/initial_setup_run_once.sh

scripts/bash/initial_build_db.sh

scripts/bash/makedict.sh



