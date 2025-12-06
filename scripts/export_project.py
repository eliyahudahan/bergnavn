import os
import datetime

# Allowed safe text file extensions
SAFE_EXTENSIONS = {".py", ".json", ".yaml", ".yml", ".txt", ".ini", ".md"}

# Max number of lines per exported chunk file
MAX_LINES = 2000


def collect_files(base_dir):
    """
    Walk through the backend directory and collect only safe text-based files.
    """
    collected = []
    for root, _, files in os.walk(base_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in SAFE_EXTENSIONS:
                collected.append(os.path.join(root, f))
    return collected


def read_file_safely(path):
    """
    Read a file safely, return content or an error message.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"ERROR READING FILE: {e}\n"


def export_to_chunks(files, output_dir):
    """
    Export all files into multiple chunked .txt files.
    Each chunk contains up to MAX_LINES lines.
    Files are never split across chunks.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    chunk_index = 1
    current_lines = 0
    current_buffer = []

    def save_chunk(buffer, idx):
        """Save a chunk to a text file."""
        filename = os.path.join(output_dir, f"export_{timestamp}_part{idx}.txt")
        with open(filename, "w", encoding="utf-8") as out:
            out.write("===== GROUP START =====\n\n")
            out.write("".join(buffer))
            out.write("\n===== GROUP END =====\n")
        print(f"✔ Saved {filename}")

    for f in files:
        rel = os.path.relpath(f)
        header = f"\n--- FILE: {rel} ---\n"
        content = read_file_safely(f)

        file_block = header + content + "\n"
        file_block_lines = file_block.count("\n")

        # If adding this file exceeds max chunk size → save and start new chunk
        if current_lines + file_block_lines > MAX_LINES and current_buffer:
            save_chunk(current_buffer, chunk_index)
            chunk_index += 1
            current_buffer = []
            current_lines = 0

        current_buffer.append(file_block)
        current_lines += file_block_lines

    # Save the last chunk
    if current_buffer:
        save_chunk(current_buffer, chunk_index)


if __name__ == "__main__":
    # Detect root directory (where the script is executed)
    root_dir = os.getcwd()

    # Backend should be inside root directory
    backend_dir = os.path.join(root_dir, "backend")

    if not os.path.isdir(backend_dir):
        raise RuntimeError(f"backend folder not found at: {backend_dir}")

    print(f"📂 Scanning backend: {backend_dir}")

    # Prepare output directory
    output_dir = os.path.join(root_dir, "export_chunks")
    os.makedirs(output_dir, exist_ok=True)

    # Collect and export
    files = collect_files(backend_dir)
    print(f"Found {len(files)} safe text files.")

    export_to_chunks(files, output_dir)

    print("🎉 Export completed.")
