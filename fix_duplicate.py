import re

html_file = "backend/templates/maritime_split/dashboard_base.html"

with open(html_file, 'r') as f:
    lines = f.readlines()

# מצא וסנן כפילויות
enhanced_count = 0
new_lines = []

for line in lines:
    if 'enhanced_dashboard_buttons.js' in line:
        enhanced_count += 1
        if enhanced_count == 1:
            new_lines.append(line)  # שמור רק את הראשון
        else:
            print(f"🗑️  Removing duplicate: {line.strip()}")
    else:
        new_lines.append(line)

# שמור אם היה שינוי
if enhanced_count > 1:
    with open(html_file, 'w') as f:
        f.writelines(new_lines)
    print(f"✅ Fixed: Removed {enhanced_count - 1} duplicate(s)")
else:
    print("✅ No duplicates found")

# בדוק את התוצאה
print("\n📋 Final check:")
with open(html_file, 'r') as f:
    content = f.read()
    matches = re.findall(r'enhanced_dashboard_buttons\.js', content)
    print(f"Found {len(matches)} occurrences of enhanced_dashboard_buttons.js")
