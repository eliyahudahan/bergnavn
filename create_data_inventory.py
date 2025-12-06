#!/usr/bin/env python3
import os
import re

# --- Collect all files with real data extensions ---
DATA_EXTENSIONS = {".json", ".csv", ".parquet"}

def collect_data_files(base_dir):
    data_files = []
    for root, _, files in os.walk(base_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in DATA_EXTENSIONS:
                data_files.append(os.path.join(root, f))
    return data_files


# --- Detect API usage in Python files ---
API_KEYWORDS = [
    "openweather", "met.no", "api", "requests.get",
    "ais", "marine", "vessel", "weather"
]

def scan_api_usage(base_dir):
    api_hits = []
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.endswith(".py"):
                full_path = os.path.join(root, f)
                try:
                    text = open(full_path, "r", encoding="utf-8").read()
                except:
                    continue

                for keyword in API_KEYWORDS:
                    if keyword.lower() in text.lower():
                        api_hits.append((full_path, keyword))
    return api_hits


# --- Detect services dealing with data ---
def scan_services(base_dir):
    service_hits = []
    for root, _, files in os.walk(base_dir):
        for f in files:
            if "service" in f.lower() and f.endswith(".py"):
                service_hits.append(os.path.join(root, f))
    return service_hits


# --- Dump inventory into a single clean text file ---
def write_inventory(output_file, data_files, api_hits, service_hits):
    with open(output_file, "w", encoding="utf-8") as out:
        out.write("===== PROJECT DATA INVENTORY =====\n\n")

        out.write("### Data Files Detected (real datasets)\n")
        for f in data_files:
            out.write(f" - {f}\n")

        out.write("\n### API Usage Detected\n")
        for path, keyword in api_hits:
            out.write(f" - {path}  (keyword: {keyword})\n")

        out.write("\n### Data-Related Services\n")
        for s in service_hits:
            out.write(f" - {s}\n")

        out.write("\n===== END OF INVENTORY =====\n")


# --- Main Execution ---
if __name__ == "__main__":
    base_dir = os.path.abspath("backend")
    output_file = "project_data_inventory.txt"

    data_files = collect_data_files(base_dir)
    api_hits = scan_api_usage(base_dir)
    service_hits = scan_services(base_dir)

    write_inventory(output_file, data_files, api_hits, service_hits)

    print("Inventory created:", output_file)
