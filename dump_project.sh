#!/bin/bash

# ==========================================================
# Project Dump Script - Topic-based, max ~2000 lines per file
# All comments must remain in English (requested).
# This script:
# 1. Defines topics
# 2. Collects files for each topic
# 3. Writes each topic into multiple chunk files
#    without breaking any file in the middle.
# 4. Ensures filenames contain no spaces.
# ==========================================================

set -e

timestamp=$(date +"%Y%m%d_%H%M")
output_dir="export_chunks"
mkdir -p "$output_dir"

MAX_LINES=2000

# Function to start a new chunk file
start_new_chunk() {
    chunk_counter=$((chunk_counter + 1))
    current_file="${output_dir}/${topic}_${timestamp}_chunk$(printf "%03d" $chunk_counter).txt"
    echo ">>> Creating $current_file"
    echo "### Topic: $topic" > "$current_file"
    echo "### Created: $timestamp" >> "$current_file"
    echo "========================================" >> "$current_file"
    current_lines=3
}

# ----------------------------------------------------------
# Define topics and associated file patterns
# ----------------------------------------------------------

declare -A TOPICS
TOPICS=(
    ["python"]="*.py"
    ["backend"]="backend/*"
    ["frontend"]="frontend/*"
    ["configs"]="*.env *.ini *.cfg requirements.txt"
    ["database"]="database/* migrations/*"
    ["scripts"]="scripts/* *.sh"
    ["docs"]="docs/* readme.md"
)

# ----------------------------------------------------------
# Iterate topics
# ----------------------------------------------------------
for topic in "${!TOPICS[@]}"; do
    echo "Processing topic: $topic"
    chunk_counter=0
    current_lines=999999  # force new chunk immediately

    # Expand file patterns
    for pattern in ${TOPICS[$topic]}; do
        for file in $(find . -type f -name "$pattern" 2>/dev/null); do

            # Skip virtual environments
            [[ "$file" == *"venv/"* ]] && continue
            [[ "$file" == *"myenv/"* ]] && continue

            # Count file lines
            file_lines=$(wc -l < "$file")

            # Start new chunk if required
            if (( current_lines + file_lines + 5 > MAX_LINES )); then
                start_new_chunk
            fi

            {
                echo ""
                echo "===== FILE: $file ====="
                cat "$file"
                echo ""
            } >> "$current_file"

            current_lines=$((current_lines + file_lines + 5))

        done
    done

done

echo "Done. Files saved in $output_dir/"
