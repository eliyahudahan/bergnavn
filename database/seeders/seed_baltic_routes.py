import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app import create_app
from backend.extensions import db
from backend.models.route import Route
from backend.models.voyage_leg import VoyageLeg
from backend.models.port import Port


app = create_app(start_scheduler=False)

def seed_ports():
    ports_data = [
        "Stockholm", "Visby", "Riga", "Klaipeda",
        "Gdansk", "Warnemuende", "Copenhagen"
    ]

    for port_name in ports_data:
        exists = Port.query.filter_by(name=port_name).first()
        if not exists:
            port = Port(name=port_name, is_active=True)
            db.session.add(port)
    db.session.commit()

def seed_baltic_route():
    baltic_route = Route.query.filter_by(name="Baltic Highlights").first()
    if not baltic_route:
        baltic_route = Route(name="Baltic Highlights", is_active=True)
        db.session.add(baltic_route)
        db.session.commit()

    ports = {port.name: port for port in Port.query.filter(Port.name.in_([
        "Stockholm", "Visby", "Riga", "Klaipeda", "Gdansk", "Warnemuende", "Copenhagen"
    ])).all()}

    # מחיקת רגלי מסלול קיימות
    VoyageLeg.query.filter_by(route_id=baltic_route.id).delete()
    db.session.commit()  # commit אחרי מחיקה

    legs_data = [
        ("Stockholm", "Visby"),
        ("Visby", "Riga"),
        ("Riga", "Klaipeda"),
        ("Klaipeda", "Gdansk"),
        ("Gdansk", "Warnemuende"),
        ("Warnemuende", "Copenhagen"),
    ]

    for dep_name, arr_name in legs_data:
        dep_port = ports.get(dep_name)
        arr_port = ports.get(arr_name)
        if dep_port and arr_port:
            leg = VoyageLeg(
                route_id=baltic_route.id,
                departure_port_id=dep_port.id,
                arrival_port_id=arr_port.id,
                is_active=True
            )
            db.session.add(leg)

    db.session.commit()

with app.app_context():
    seed_ports()
    seed_baltic_route()
    print("✅ Baltic routes seeded successfully!")
