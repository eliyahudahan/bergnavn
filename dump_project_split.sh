#!/bin/bash

# Exit on errors
set -e

OUTPUT_DIR="export_chunks"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$OUTPUT_DIR"

echo "📦 Creating split project dump in: $OUTPUT_DIR"

###############################################
# Helper function — split output into < 2000 lines
###############################################
split_output() {
    local category="$1"
    local command="$2"

    echo "→ Processing: $category"

    tmpfile=$(mktemp)
    eval "$command" > "$tmpfile"

    total_lines=$(wc -l < "$tmpfile")

    if [ "$total_lines" -le 2000 ]; then
        out="$OUTPUT_DIR/${category}_${TIMESTAMP}.txt"
        mv "$tmpfile" "$out"
        echo "✔ Saved $out ($total_lines lines)"
    else
        echo "⚠ $category exceeds 2000 lines — splitting"
        split -l 2000 "$tmpfile" "$OUTPUT_DIR/${category}_${TIMESTAMP}_part_"
        rm "$tmpfile"
        echo "✔ Split into multiple parts"
    fi
}

###############################################
# 1. Project structure
###############################################
split_output "project_structure" \
"find . -maxdepth 8 -type f | sort"

###############################################
# 2. Python code
###############################################
split_output "python_code" \
"find backend -type f -iname '*.py' -exec sed 's/^/>>> /' {} +"

###############################################
# 3. JSON maritime route data
###############################################
split_output \"json_routes\" \
\"find backend/assets/routeinfo_routes -type f -iname '*.json' -exec echo '=== {} ===' \; -exec cat {} \;\"

###############################################
# 4. Config files (.env, config.py, etc.)
###############################################
split_output "configs" \
"cat backend/config/config.py example.env 2>/dev/null"

###############################################
# 5. Requirements / dependencies
###############################################
split_output "requirements" \
"cat requirements.txt 2>/dev/null"

###############################################
# 6. Metadata, tools, scripts
###############################################
split_output "scripts" \
"find scripts -type f -exec echo '=== {} ===' \; -exec cat {} \;"

###############################################
# Done!
###############################################
echo "🎉 Done! Files saved under: $OUTPUT_DIR/"
