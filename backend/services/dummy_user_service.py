from backend.models.dummy_user import DummyUser
from backend.config import flags
from backend import db

def create_dummy_user(username, email=None, scenario=None, user_flags=None,
                      gender=None, nationality=None, language=None, preferred_sailing_areas=None):

    current_count = DummyUser.query.filter_by(active=True).count()
    if current_count >= flags.MAX_DUMMY_USERS:  # flags מהקונפיג
        raise ValueError(f"Exceeded maximum allowed dummy users ({flags.MAX_DUMMY_USERS})")

    user = DummyUser(
        username=username,
        email=email,
        scenario=scenario,
        flags=user_flags or {},  # ← זה הפתרון לשגיאה שלך
        gender=gender,
        nationality=nationality,
        language=language,
        preferred_sailing_areas=preferred_sailing_areas
    )

    db.session.add(user)
    db.session.commit()
    return user

def get_all_dummy_users():
    return DummyUser.query.all()

def deactivate_dummy_user(user_id):
    user = DummyUser.query.get(user_id)
    if user:
        user.active = False
        db.session.commit()
