# backend/services/timezone_service.py

from timezonefinder import TimezoneFinder
import pytz
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="bergnavn_cruise_app")
tf = TimezoneFinder()

def get_timezone_from_city(city_name):
    try:
        location = geolocator.geocode(city_name)
        if not location:
            return None
        timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
        return timezone_str
    except Exception as e:
        print(f"Error in timezone lookup: {e}")
        return None
