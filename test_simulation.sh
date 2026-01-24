#!/bin/bash
echo "🧪 TESTING SIMULATION FIXES"
echo "============================"

# Test 1: Check if template file exists
echo "1. Checking template file..."
if [ -f "backend/templates/maritime_split/realtime_simulation.html" ]; then
    echo "   ✅ Template exists"
    
    # Check for template errors
    BLOCK_COUNT=$(grep -c "{% block" backend/templates/maritime_split/realtime_simulation.html)
    ENDBLOCK_COUNT=$(grep -c "{% endblock" backend/templates/maritime_split/realtime_simulation.html)
    
    if [ "$BLOCK_COUNT" -eq "$ENDBLOCK_COUNT" ]; then
        echo "   ✅ Template blocks balanced: $BLOCK_COUNT blocks"
    else
        echo "   ⚠️  Block mismatch: $BLOCK_COUNT blocks vs $ENDBLOCK_COUNT endblocks"
    fi
    
else
    echo "   ❌ Template not found"
fi

# Test 2: Check simulation core
echo ""
echo "2. Checking simulation core..."
if [ -f "backend/static/js/split/simulation_core.js" ]; then
    echo "   ✅ Simulation core exists"
    echo "   📊 First few lines:"
    head -5 backend/static/js/split/simulation_core.js | sed 's/^/      /'
else
    echo "   ❌ Simulation core not found"
fi

# Test 3: Check for empirical data references
echo ""
echo "3. Checking for empirical data in template..."
EMPIRICAL_COUNT=$(grep -c -i "empirical\|validation\|statistical\|fuel.*sav" backend/templates/maritime_split/realtime_simulation.html)
echo "   ✅ Found $EMPIRICAL_COUNT empirical data references"

# Test 4: Check for ROI and fuel savings
echo ""
echo "4. Checking for ROI and fuel savings..."
ROI_COUNT=$(grep -c -i "roi\|return.*investment\|fuel.*sav" backend/templates/maritime_split/realtime_simulation.html)
echo "   ✅ Found $ROI_COUNT ROI/fuel savings references"

echo ""
echo "============================"
echo "📋 SUMMARY:"
echo "- Template: $( [ -f "backend/templates/maritime_split/realtime_simulation.html" ] && echo "✅" || echo "❌" )"
echo "- Simulation Core: $( [ -f "backend/static/js/split/simulation_core.js" ] && echo "✅" || echo "❌" )"
echo "- Blocks Balanced: $( [ "$BLOCK_COUNT" -eq "$ENDBLOCK_COUNT" ] 2>/dev/null && echo "✅" || echo "❌" )"
echo "- Empirical Data: $( [ "$EMPIRICAL_COUNT" -gt 5 ] && echo "✅" || echo "❌" )"
echo "- ROI References: $( [ "$ROI_COUNT" -gt 2 ] && echo "✅" || echo "❌" )"
echo ""
echo "🚀 To start the simulation:"
echo "   cd ~/dev/bergnavn"
echo "   python app.py"
echo "   Then visit: http://localhost:5000/maritime/simulation"
