from backend.extensions import db
from backend.models.port import Port
from backend.services.geocode_service import GeoCodeService

def add_or_update_port(name, country=None):
    if country:
        port = Port.query.filter_by(name=name, country=country).first()
    else:
        matches = Port.query.filter_by(name=name).all()
        if len(matches) == 1:
            port = matches[0]
        elif len(matches) == 0:
            port = None
        else:
            raise Exception(f"Multiple ports found for city '{name}'. Please specify a country.")

    if port:
        return port

    lat, lon, detected_country = GeoCodeService.get_location_info(name)
    if lat is None or lon is None:
        raise Exception(f"Could not find coordinates for port '{name}'")

    country_to_use = country or detected_country

    port = Port(name=name, country=country_to_use, latitude=lat, longitude=lon)
    db.session.add(port)
    db.session.commit()
    return port


