#!/usr/bin/env bash
#
# Usage:
#   ./projectStructureCollector.sh <targetFolder> <outputFile.txt> [ignoredPaths...]
#
# Example:
#   ./projectStructureCollector.sh ./ ./structure.txt data/someFolder node_modules build .git
#
# Explanation:
#   - The script will list the entire folder structure of <targetFolder>
#   - Writes the resulting hierarchy to <outputFile.txt>
#   - Skips any paths that match the relative path (e.g., "data/someFolder") or the basename
#     (e.g., "node_modules") from the ignoredPaths list.

# Exit on error or using an uninitialized variable
#set -o errexit
set -o nounset

###############################################################################
# 1. Parse arguments
###############################################################################
if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <targetFolder> <outputFile.txt> [ignoredPaths...]"
  exit 1
fi

targetFolder="$1"
outputFile="$2"
shift 2
ignoredList=("$@")

# Convert targetFolder to an absolute path
targetFolderAbsolute="$(cd "$targetFolder" && pwd)"

# Clear (or create) the output file
> "$outputFile"

###############################################################################
# 2. Define function to print folder structure
###############################################################################
print_structure() {
  local folder="$1"
  local indent="$2"

  # Base name of the current folder (e.g. "data", "scripts", etc.)
  local baseName
  baseName="$(basename "$folder")"

  # Compute the relative path using Python (since macOS's realpath doesn't support --relative-to)
  local relativePath
  relativePath="$(python3 -c 'import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))' "$folder" "$targetFolderAbsolute")"

  # Normalize the relative path (remove any trailing slash)
  local normalizedRelativePath="${relativePath%/}"

  # ---------------------------------------------------------------------------
  # (A) Check if we should ignore this folder
  # ---------------------------------------------------------------------------
  for ignored in "${ignoredList[@]}"; do
    # Normalize the ignored path as well (remove trailing slash if any)
    local normalizedIgnored="${ignored%/}"
    # If the normalized relative path matches exactly the ignored path
    if [[ "$normalizedRelativePath" == "$normalizedIgnored" ]]; then
      return
    fi
    # Or if the folder name alone matches the ignored pattern
    if [[ "$baseName" == "$normalizedIgnored" ]]; then
      return
    fi
  done

  # ---------------------------------------------------------------------------
  # (B) Print the current folder
  # ---------------------------------------------------------------------------
  echo "${indent}${baseName}/" >> "$outputFile"

  # ---------------------------------------------------------------------------
  # (C) Get contents of the folder (files, subfolders). If there's an error,
  #     or it's unreadable, skip it gracefully.
  # ---------------------------------------------------------------------------
  local entries=()
  { entries=("$folder"/*); } 2>/dev/null || true

  # If expansion gave us no valid entry (like an empty folder or unreadable directory),
  # then skip further processing.
  if [ ! -e "${entries[0]:-}" ]; then
    return
  fi

  # ---------------------------------------------------------------------------
  # (D) Recursively process each item
  # ---------------------------------------------------------------------------
  for entry in "${entries[@]}"; do
    if [ -d "$entry" ]; then
      # Subfolder: recurse with an additional indent
      print_structure "$entry" "  $indent"
    else
      # File: print with indentation
      echo "  ${indent}$(basename "$entry")" >> "$outputFile"
    fi
  done
}

###############################################################################
# 3. Begin recursion from the target folder
###############################################################################
print_structure "$targetFolderAbsolute" ""

###############################################################################
# 4. Done
###############################################################################
echo "Project hierarchy written to: $outputFile"
exit 0
