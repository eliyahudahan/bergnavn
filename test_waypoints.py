import requests
from bs4 import BeautifulSoup
import json

# קבל את הדף
response = requests.get('http://localhost:5000/maritime/dashboard?lang=en')
soup = BeautifulSoup(response.text, 'html.parser')

# מצא את אלמנט waypoints-data
waypoints_elem = soup.find('div', {'id': 'waypoints-data'})
if waypoints_elem and waypoints_elem.text:
    try:
        data = json.loads(waypoints_elem.text)
        print(f"✅ waypoints-data found with {len(data)} routes")
        if len(data) > 0:
            first_key = list(data.keys())[0]
            print(f"First route key: {first_key}")
            print(f"Waypoints count: {len(data[first_key])}")
            print(f"Sample waypoint: {data[first_key][0] if data[first_key] else 'None'}")
    except Exception as e:
        print(f"❌ Error parsing waypoints: {e}")
else:
    print("❌ waypoints-data element not found or empty")

# מצא את אלמנט routes-data
routes_elem = soup.find('div', {'id': 'routes-data'})
if routes_elem and routes_elem.text:
    try:
        routes = json.loads(routes_elem.text)
        print(f"\n✅ routes-data found with {len(routes)} routes")
        if len(routes) > 0:
            print(f"First route: {routes[0].get('clean_name', 'Unknown')}")
            print(f"Has waypoints in route object: {'waypoints' in routes[0]}")
    except Exception as e:
        print(f"❌ Error parsing routes: {e}")
