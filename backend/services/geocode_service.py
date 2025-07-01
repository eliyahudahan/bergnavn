import requests

class GeoCodeService:
    @staticmethod
    def get_location_info(name):
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": name,
            "format": "json",
            "addressdetails": 1,
            "limit": 1
        }
        headers = {
            "User-Agent": "BergNavnApp/1.5 framgangsrik747@gmail.com"  # חשוב להכניס מייל או שם מזהה
        }
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not data:
            return None, None, None

        result = data[0]
        lat = float(result["lat"])
        lon = float(result["lon"])
        country = result["address"].get("country")

        return lat, lon, country

