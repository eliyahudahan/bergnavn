#!/bin/bash
# fix_simulation_template.sh - Fix missing endblock in realtime_simulation.html

echo "🔧 Fixing simulation template syntax error..."

# Check current end of file
echo "Current last lines:"
tail -n 5 backend/templates/maritime_split/realtime_simulation.html

# Create backup
cp backend/templates/maritime_split/realtime_simulation.html \
   backend/templates/maritime_split/realtime_simulation.html.backup

echo "Creating corrected template..."

# Create the corrected file ending
cat > /tmp/corrected_end.html << 'EOF'
</script>
{% endblock %}
EOF

# Remove just the last line if it has syntax error
sed -i '$ d' backend/templates/maritime_split/realtime_simulation.html

# Add the corrected ending
cat /tmp/corrected_end.html >> backend/templates/maritime_split/realtime_simulation.html

echo "✅ Fixed! New last lines:"
tail -n 5 backend/templates/maritime_split/realtime_simulation.html
echo ""
echo "📁 Backup saved to: realtime_simulation.html.backup"
echo "🔄 Restart Flask server to see changes"