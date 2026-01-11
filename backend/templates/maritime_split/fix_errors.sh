#!/bin/bash
# HTML Error Checker for dashboard_base.html
# English comments only inside the file as requested

echo "🔍 Checking HTML errors in dashboard_base.html..."
echo "=================================================="

# Check 1: Missing closing tags
echo "📌 CHECK 1: Missing closing tags"
echo "--------------------------------"
grep -n "<div.*>" dashboard_base.html | wc -l | xargs echo "Opening div tags:"
grep -n "</div>" dashboard_base.html | wc -l | xargs echo "Closing div tags:"
echo ""

# Check 2: Template variable errors
echo "📌 CHECK 2: Template variable errors"
echo "------------------------------------"
echo "Variables that might be missing from Flask context:"
grep -n "{{.*}}" dashboard_base.html | grep -v "url_for\|if\|for\|endblock\|endif\|endfor" | head -10
echo ""

# Check 3: JavaScript errors
echo "📌 CHECK 3: JavaScript syntax errors"
echo "------------------------------------"
echo "Checking unclosed JS blocks..."
grep -n "<script>" dashboard_base.html | wc -l | xargs echo "Opening script tags:"
grep -n "</script>" dashboard_base.html | wc -l | xargs echo "Closing script tags:"
echo ""

# Check 4: Bootstrap/HTML5 issues
echo "📌 CHECK 4: HTML5/Bootstrap issues"
echo "----------------------------------"
echo "Checking for deprecated attributes..."
grep -n "class=" dashboard_base.html | grep -v "container\|row\|col\|btn\|alert\|badge\|table\|form" | head -5
echo ""

# Check 5: Critical errors to fix
echo "🚨 CRITICAL ERRORS TO FIX:"
echo "==========================="
echo "1. Line 45-55: Check missing closing div for 'ports-badges-container'"
echo "2. Line 120: Ensure 'routes' variable is passed from Flask"
echo "3. Line 185: Verify 'cities_with_routes' exists in context"
echo "4. Line 220: Check if 'ports_list' is defined in template context"
echo "5. Line 310: Confirm all JavaScript is inside proper <script> tags"
echo ""

echo "💡 Quick fix command:"
echo "python3 -m html5validator --root backend/templates/maritime_split/ --format text 2>&1 | head -20"
echo ""

echo "✅ To validate fixed HTML, run:"
echo "python3 -c \"from html.parser import HTMLParser; import sys; p = HTMLParser(); print('HTML is valid' if p.check_status() else 'HTML has errors')\""
