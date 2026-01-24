# תיקיה: bergnavn/check_rtz_format.py

#!/usr/bin/env python3
"""
Check the actual structure of RTZ files from Kystverket
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path

def check_rtz_structure(rtz_file: str):
    """Check the structure of an RTZ file."""
    print(f"\n🔍 Checking: {os.path.basename(rtz_file)}")
    print("=" * 50)
    
    try:
        # Read the file
        with open(rtz_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Print first 500 characters
        print("First 500 chars:")
        print(content[:500])
        print("-" * 50)
        
        # Try to parse XML
        root = ET.fromstring(content)
        
        # Get all unique tags
        all_tags = set()
        
        def get_all_tags(element, prefix=''):
            tag = element.tag
            # Remove namespace if present
            if '}' in tag:
                tag = tag.split('}', 1)[1]
            all_tags.add(tag)
            
            for child in element:
                get_all_tags(child, prefix + '  ')
        
        get_all_tags(root)
        
        print("Unique tags found:")
        for tag in sorted(all_tags):
            print(f"  - {tag}")
        
        # Specifically look for routeInfo and waypoints
        print("\nLooking for specific elements:")
        
        # Try with namespace
        for elem in root.iter():
            tag = elem.tag
            if 'routeInfo' in tag or 'RouteInfo' in tag:
                print(f"Found routeInfo-like element: {tag}")
                print(f"  Attributes: {elem.attrib}")
            
            if 'waypoint' in tag.lower() or 'Waypoint' in tag:
                print(f"Found waypoint-like element: {tag}")
                print(f"  Attributes: {elem.attrib}")
        
        # Try without namespace
        print("\nChecking without namespace considerations:")
        for elem in root.iter():
            # Remove namespace
            tag = elem.tag
            if '}' in tag:
                tag = tag.split('}', 1)[1]
            
            if tag.lower() == 'routeinfo':
                print(f"Found routeInfo (no namespace):")
                print(f"  Attributes: {elem.attrib}")
                for child in elem:
                    print(f"    Child: {child.tag} = {child.text}")
            
            if tag.lower() == 'waypoint':
                print(f"Found waypoint (no namespace):")
                print(f"  Attributes: {elem.attrib}")
                for child in elem:
                    child_tag = child.tag
                    if '}' in child_tag:
                        child_tag = child_tag.split('}', 1)[1]
                    print(f"    Child: {child_tag} = {child.text or child.attrib}")
        
        # Look for any coordinates
        print("\nLooking for coordinates:")
        for elem in root.iter():
            if 'lat' in elem.attrib or 'lon' in elem.attrib:
                tag = elem.tag
                if '}' in tag:
                    tag = tag.split('}', 1)[1]
                print(f"Found coordinates in {tag}: {elem.attrib}")
        
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        # Try to see what we have
        lines = content.split('\n')
        print("First 10 lines:")
        for i, line in enumerate(lines[:10]):
            print(f"{i+1}: {line}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    # Check a sample file from each city
    base_path = "backend/assets/routeinfo_routes"
    
    # Get first city with files
    for city in os.listdir(base_path):
        city_path = os.path.join(base_path, city, 'raw')
        if os.path.exists(city_path):
            # Look for extracted files
            extracted_path = os.path.join(base_path, city, 'extracted')
            if os.path.exists(extracted_path):
                rtz_files = [f for f in os.listdir(extracted_path) if f.endswith('.rtz')]
                if rtz_files:
                    sample_file = os.path.join(extracted_path, rtz_files[0])
                    check_rtz_structure(sample_file)
                    return  # Just check one file for now
    
    # If no extracted files, check the raw ZIP content
    print("No extracted files found. Checking a ZIP file directly...")
    
    for city in os.listdir(base_path):
        city_path = os.path.join(base_path, city, 'raw')
        if os.path.exists(city_path):
            zip_files = [f for f in os.listdir(city_path) if f.endswith('_routes.rtz')]
            if zip_files:
                import zipfile
                zip_path = os.path.join(city_path, zip_files[0])
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        # Extract first RTZ file
                        rtz_in_zip = [f for f in zip_ref.namelist() if f.endswith('.rtz')]
                        if rtz_in_zip:
                            # Extract to temp
                            import tempfile
                            with tempfile.TemporaryDirectory() as tmpdir:
                                zip_ref.extract(rtz_in_zip[0], tmpdir)
                                rtz_file = os.path.join(tmpdir, rtz_in_zip[0])
                                # Read and check
                                with open(rtz_file, 'r', encoding='utf-8') as f:
                                    content = f.read(1000)
                                    print(f"\nFirst 1000 chars of {rtz_in_zip[0]}:")
                                    print(content)
                except:
                    pass

if __name__ == "__main__":
    main()