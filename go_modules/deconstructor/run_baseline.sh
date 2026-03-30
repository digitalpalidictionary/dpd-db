#!/bin/bash
set -e

# Change to the root of the project where config.ini is located
cd "$(dirname "$0")/../.." || exit 1

export DPD_DECONSTRUCTOR_BASELINE=20000

echo "Starting baseline test with DPD_DECONSTRUCTOR_BASELINE=$DPD_DECONSTRUCTOR_BASELINE"

# Time the execution
time go run ./go_modules/deconstructor

echo "Computing SHA256 hashes of output files..."
sha256sum go_modules/deconstructor/output/matches.tsv
sha256sum go_modules/deconstructor/output/unmatched.tsv
