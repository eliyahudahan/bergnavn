from backend.extensions import db
from backend.models.cruise import Cruise
from backend.models.voyage_leg import VoyageLeg
from datetime import datetime, timedelta, UTC
from app import create_app

# Init app and context
app = create_app()
with app.app_context():
    # Create a cruise
    cruise = Cruise(
        title="Scandinavian Discovery",
        description="Cruise through the beautiful Scandinavian ports",
        departure_date=datetime(2025, 7, 10, 10, 0, tzinfo=UTC),
        return_date=datetime(2025, 7, 20, 18, 0, tzinfo=UTC),
        origin="Copenhagen",
        destination="Helsinki",
        price=1450.0,
        capacity=120
    )

    # Create voyage legs
    leg1 = VoyageLeg(
        departure_port="Copenhagen",
        arrival_port="Oslo",
        departure_time=datetime(2025, 7, 10, 10, 0, tzinfo=UTC),
        arrival_time=datetime(2025, 7, 11, 8, 0, tzinfo=UTC),
        leg_order=1
    )
    leg2 = VoyageLeg(
        departure_port="Oslo",
        arrival_port="Stockholm",
        departure_time=datetime(2025, 7, 11, 18, 0, tzinfo=UTC),
        arrival_time=datetime(2025, 7, 13, 9, 0, tzinfo=UTC),
        leg_order=2
    )
    leg3 = VoyageLeg(
        departure_port="Stockholm",
        arrival_port="Helsinki",
        departure_time=datetime(2025, 7, 14, 8, 0, tzinfo=UTC),
        arrival_time=datetime(2025, 7, 15, 14, 0, tzinfo=UTC),
        leg_order=3
    )

    # Associate legs with cruise
    cruise.legs = [leg1, leg2, leg3]

    # Add to session and commit
    db.session.add(cruise)
    db.session.commit()

    print(f"✅ Cruise created: {cruise}")
    for leg in cruise.legs:
        print(f"  ↳ {leg}")

