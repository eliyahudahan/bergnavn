import os
import zipfile

# Root directory for all RTZ sources
ROOT = "backend/assets/routeinfo_routes"

def extract_rtz_files():
    for subdir, _, files in os.walk(ROOT):
        if "raw" not in subdir:
            continue
        for file in files:
            if file.endswith(".rtz"):
                rtz_path = os.path.join(subdir, file)
                extract_dir = os.path.join(subdir, "extracted")
                os.makedirs(extract_dir, exist_ok=True)

                try:
                    with zipfile.ZipFile(rtz_path, "r") as z:
                        z.extractall(extract_dir)
                        print(f"✅ Extracted {file} → {extract_dir}")
                except zipfile.BadZipFile:
                    print(f"❌ Skipped (corrupt or not zip): {rtz_path}")

if __name__ == "__main__":
    extract_rtz_files()
