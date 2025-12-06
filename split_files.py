import os

# --- Utility: Read a file safely ---
def read_file(path):
    """Read file content safely with UTF-8 encoding."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# --- Utility: Write output file ---
def write_file(path, content):
    """Write content to a file using UTF-8 encoding."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# --- Split maritime.js into logical modules ---
def split_maritime_js(base_dir):
    """Split maritime.js into logical modules based on section markers."""
    js_path = os.path.join(base_dir, "static", "js", "maritime.js")

    content = read_file(js_path)

    sections = {
        "maritime_core.js": [],
        "maritime_weather.js": [],
        "maritime_map.js": [],
        "maritime_analytics.js": []
    }

    current_section = "maritime_core.js"

    # Assign lines based on comment markers
    for line in content.split("\n"):
        if "// WEATHER SECTION" in line:
            current_section = "maritime_weather.js"
        elif "// MAP SECTION" in line:
            current_section = "maritime_map.js"
        elif "// ANALYTICS SECTION" in line:
            current_section = "maritime_analytics.js"

        sections[current_section].append(line)

    output_dir = os.path.join(base_dir, "static", "js", "split")
    os.makedirs(output_dir, exist_ok=True)

    for filename, lines in sections.items():
        write_file(os.path.join(output_dir, filename), "\n".join(lines))

    return output_dir

# --- Split maritime_dashboard.html into logical modular templates ---
def split_dashboard_html(base_dir):
    """Split dashboard HTML into logical widget files."""
    html_path = os.path.join(base_dir, "templates", "maritime_dashboard.html")
    content = read_file(html_path)

    sections = {
        "dashboard_base.html": [],
        "dashboard_weather_widget.html": [],
        "dashboard_map_widget.html": [],
        "dashboard_analytics_widget.html": []
    }

    current_section = "dashboard_base.html"

    for line in content.split("\n"):
        if "<!-- WEATHER WIDGET -->" in line:
            current_section = "dashboard_weather_widget.html"
        elif "<!-- MAP WIDGET -->" in line:
            current_section = "dashboard_map_widget.html"
        elif "<!-- ANALYTICS WIDGET -->" in line:
            current_section = "dashboard_analytics_widget.html"

        sections[current_section].append(line)

    output_dir = os.path.join(base_dir, "templates", "maritime_split")
    os.makedirs(output_dir, exist_ok=True)

    for filename, lines in sections.items():
        write_file(os.path.join(output_dir, filename), "\n".join(lines))

    return output_dir

# --- Main execution ---
if __name__ == "__main__":
    # Runs from project root
    base_dir = os.path.join(os.getcwd(), "backend")
    print(f"Using backend directory: {base_dir}")

    js_out = split_maritime_js(base_dir)
    html_out = split_dashboard_html(base_dir)

    print("\n=== Split Completed Successfully ===")
    print(f"JS Output: {js_out}")
    print(f"HTML Output: {html_out}")
