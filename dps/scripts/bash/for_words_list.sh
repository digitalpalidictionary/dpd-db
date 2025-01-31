#!/bin/bash

# Set input and output CSV files
input_csv="temp/input.csv"
output_csv="temp/output.csv"

# Set directory paths for Pali text dataset and English translation
basedir="resources/sc-data/sc_bilara_data"
srcfolder="${basedir}/root/pli/ms/vinaya/pli-tv-kd"
trnfiolder="${basedir}/translation/en/brahmali/vinaya/pli-tv-kd"
varfolder="${basedir}/variant"

# Define clearSearch function
function clearSearch() {
    sed 's/.*.json://g' | sed 's/:.*": "/ /g'| sed 's/ ",//g' | sed 's/"pli-tv-//g'
}

# Set separator
separator=";"

# Read input CSV file
while IFS=, read -r word; do
    echo -n "$word"
    echo -n "$separator"

    # Search for word in Pali text dataset
    grep -riE -m1 "${word}" "$srcfolder"/* "$varfolder"/* | while read paliline; do
        id=$(echo "$paliline" | awk '{print $2}')
        echo -n "$paliline" | clearSearch
        echo -n "$separator"

        # Search for ID in English translation
        grep -i "$id" "$trnfiolder"/* | while read engline; do
            cleanedEngLine=$(echo "$engline" | clearSearch)

            case "$cleanedEngLine" in
                *[0-9]\.*) 
                    topic=$(echo "$cleanedEngLine" | sed 's/.*[0-9]*\. //' | awk '{ $1 = tolower($1); print }')
                    section_number=$(echo "$cleanedEngLine"  | awk '{print $2}' | sed 's/\.//')
                    khandakha=$(echo "$cleanedEngLine" | awk '{print $1}'| sed 's/kd//g')
                    result="${topic} - section #${section_number} of the khandakha #${khandakha}"
                    echo -n "$result"
                    echo -n "$separator"
                    ;;
                *)
                    echo "$cleanedEngLine"  | awk '{for (i=2; i<=NF; i++) printf $i (i<NF ? OFS : "\n")}'
                    ;;
            esac
            echo
        done
    done
    echo
done < "$input_csv" > "$output_csv"