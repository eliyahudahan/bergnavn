from backend.models.dummy_user import DummyUser
from backend import db

def create_dummy_user(username, email=None, scenario=None, flags=None,
                      gender=None, nationality=None, language=None, preferred_sailing_areas=None):
    user = DummyUser(
        username=username,
        email=email,
        scenario=scenario,
        flags=flags or {},
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
