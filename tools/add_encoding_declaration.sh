#!/bin/bash

# Script to add UTF-8 encoding declaration to Python files that perform file read operations

# Define the encoding declaration to add
ENCODING_DECLARATION="# -*- coding: utf-8 -*-"

# Define temporary file for storing list of files to process
TEMP_FILE_LIST="/tmp/python_files_to_update.txt"

# Find all Python files in the project that contain 'open(' or 'read_text('
# Exclude files in 'archive/' directory to avoid modifying old code
find . -type f -name "*.py" -not -path "./archive/*" -exec grep -lE "\bopen\s*\(|\.read_text\s*\(" {} \; > "$TEMP_FILE_LIST"

# Counter for tracking updates
UPDATED_COUNT=0
SKIPPED_COUNT=0

# Process each file
while IFS= read -r file; do
    # Check if the file already has the encoding declaration in the first two lines
    if head -n 2 "$file" | grep -q "$ENCODING_DECLARATION"; then
        echo "Skipped: $file (already has encoding declaration)"
        ((SKIPPED_COUNT++))
    else
        # Read the first line to check for shebang
        FIRST_LINE=$(head -n 1 "$file")
        if [[ "$FIRST_LINE" == "#!"* ]]; then
            # If there's a shebang, insert encoding declaration after it
            sed -i "2i $ENCODING_DECLARATION" "$file"
        else
            # Otherwise, insert at the very top
            sed -i "1i $ENCODING_DECLARATION" "$file"
        fi
        echo "Updated: $file (added encoding declaration)"
        ((UPDATED_COUNT++))
    fi
done < "$TEMP_FILE_LIST"

# Summary
echo "Summary: Updated $UPDATED_COUNT files, Skipped $SKIPPED_COUNT files."
echo "List of updated files saved to /tmp/updated_files.txt"

# Save list of updated files for reference
grep "Updated:" /tmp/updated_files_log.txt > /tmp/updated_files.txt 2>/dev/null || echo "No log file created yet."

# Clean up
rm -f "$TEMP_FILE_LIST"

echo "Done."
