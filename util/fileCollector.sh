#!/usr/bin/env bash

# Usage:
#   ./collect-files.sh /path/to/folder /path/to/output.txt [ignore_pattern1] [ignore_pattern2] ...
#   ./fileCollector.sh . ./output.txt .sh .md .pdf .txt .zip .log data/ThePublicJiraDataset/ data/var/lib/ .git .DS_Store .gitignore scripts/__pycache__/ .ipynb
#
# The first argument is the folder to scan.
# The second argument is the file in which we want to append the output.
# Additional arguments are glob patterns for files to ignore.

# Check if at least two arguments are passed
if [ "$#" -lt 2 ]; then
  echo "Usage: $0 /path/to/folder /path/to/output.txt [ignore_pattern1] [ignore_pattern2] [path/to/folder/to/ignore/]..."
  echo "Example: ./fileCollector.sh . ./output.txt .sh .git .md example.js data/ util/scripts/"
  exit 1
fi

FOLDER="$1"
OUTPUT_FILE="$2"

# Shift the first two parameters so we get ignore patterns
shift 2
IGNORE_PATTERNS=("$@")

> "$OUTPUT_FILE"

# Use 'find' to list all files (not directories) within $FOLDER, excluding the output file
find "$FOLDER" -type f ! -path "$OUTPUT_FILE" | while IFS= read -r FILE; do
  
  # Check if the file matches any of the ignore patterns
  skip=0
  for pattern in "${IGNORE_PATTERNS[@]}"; do
    if [[ "$FILE" == *"$pattern"* ]]; then
      echo "Skipping file: $FILE (matched pattern: $pattern)"
      skip=1
      break
    fi
  done
  if [ "$skip" -eq 1 ]; then
    continue
  fi
  
  # Ensure it's a regular file
  if [[ -f "$FILE" ]]; then
    # get relative path
    RELATIVE_PATH="${FILE#$FOLDER/}"

    echo "$RELATIVE_PATH:" >> "$OUTPUT_FILE"
    
    echo "<Start of file>" >> "$OUTPUT_FILE"
    cat "$FILE" >> "$OUTPUT_FILE"
    echo >> "$OUTPUT_FILE"
    echo "<End of file>" >> "$OUTPUT_FILE"

    echo >> "$OUTPUT_FILE"
  fi

done
