#!/usr/bin/env python3
"""
Update dashboard control buttons with new labels and functionality
This script modifies only the display text and tooltips, preserving all existing functionality
"""

import re

def update_html_file():
    """Update the dashboard HTML file with new button labels"""
    
    html_file = "backend/templates/maritime_split/dashboard_base.html"
    
    print(f"📄 Reading HTML file: {html_file}")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Track changes
    changes_made = 0
    
    # 1. Update RTZ Routes button
    if '<i class="fas fa-route"></i>' in content:
        # Change tooltip only - keep icon
        content = content.replace(
            'title="Toggle RTZ Routes"',
            'title="Highlight Routes"'
        )
        changes_made += 1
        print("✅ Updated: RTZ Routes → Highlight Routes")
    
    # 2. Update Real Vessels button
    if '<i class="bi bi-ship"></i>' in content:
        # Change icon and tooltip
        content = content.replace(
            '<i class="bi bi-ship"></i>',
            '<i class="bi bi-arrow-repeat"></i>'
        )
        content = content.replace(
            'title="Toggle Real Vessels"',
            'title="Refresh Data"'
        )
        changes_made += 1
        print("✅ Updated: Real Vessels → Refresh Data")
    
    # 3. Update Wind Turbines button
    if '<i class="bi bi-fan"></i>' in content:
        # Change icon and tooltip
        content = content.replace(
            '<i class="bi bi-fan"></i>',
            '<i class="bi bi-lightning-charge"></i>'
        )
        content = content.replace(
            'title="Toggle Wind Turbines"',
            'title="Turbine Status"'
        )
        changes_made += 1
        print("✅ Updated: Wind Turbines → Turbine Status")
    
    # 4. Update Tankers button
    if '<i class="bi bi-droplet"></i>' in content:
        # Change icon and tooltip
        content = content.replace(
            '<i class="bi bi-droplet"></i>',
            '<i class="bi bi-fuel-pump"></i>'
        )
        content = content.replace(
            'title="Toggle Tankers"',
            'title="Fuel Prices"'
        )
        changes_made += 1
        print("✅ Updated: Tankers → Fuel Prices")
    
    # Save updated file
    if changes_made > 0:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n✨ Successfully updated {changes_made} buttons")
        print("🔧 All button IDs preserved - no functionality broken")
    else:
        print("ℹ️ No changes needed - buttons already updated")

if __name__ == "__main__":
    update_html_file()
