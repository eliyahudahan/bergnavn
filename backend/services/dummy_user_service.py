import re
from backend.models.dummy_user import DummyUser
from backend.config import flags
from backend import db

EMAIL_REGEX = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'

def create_dummy_user(username, email=None, scenario=None, user_flags=None,
                      gender=None, nationality=None, language=None, preferred_sailing_areas=None):
    username = username.strip()
    if not username:
        raise ValueError("Username cannot be empty.")

    if DummyUser.query.filter_by(username=username, active=True).first():
        raise ValueError("Username already exists.")

    if email:
        email = email.strip()
        if not re.match(EMAIL_REGEX, email):
            raise ValueError("Invalid email format.")
        if DummyUser.query.filter_by(email=email, active=True).first():
            raise ValueError("Email already exists.")

    current_count = DummyUser.query.filter_by(active=True).count()
    if current_count >= flags.MAX_DUMMY_USERS:
        raise ValueError(f"Exceeded maximum allowed dummy users ({flags.MAX_DUMMY_USERS})")

    user = DummyUser(
        username=username,
        email=email if email else None,
        scenario=scenario,
        flags=user_flags or {},
        gender=gender,
        nationality=nationality,
        language=language,
        preferred_sailing_areas=preferred_sailing_areas,
        active=True
    )

    db.session.add(user)
    db.session.commit()
    return user

def update_dummy_user(user_id, data):
    user = DummyUser.query.get(user_id)
    if not user or not user.active:
        return False

    new_username = data.get('username', user.username).strip()
    new_email = data.get('email', user.email)
    new_email = new_email.strip() if new_email else None

    if new_username != user.username:
        if DummyUser.query.filter(DummyUser.username == new_username, DummyUser.id != user_id, DummyUser.active == True).first():
            raise ValueError("Username already exists.")

    if new_email:
        if not re.match(EMAIL_REGEX, new_email):
            raise ValueError("Invalid email format.")
        if new_email != user.email:
            if DummyUser.query.filter(DummyUser.email == new_email, DummyUser.id != user_id, DummyUser.active == True).first():
                raise ValueError("Email already exists.")

    user.username = new_username
    user.email = new_email
    user.scenario = data.get('scenario', user.scenario)
    user.flags = data.get('flags', user.flags)
    user.gender = data.get('gender', user.gender)
    user.nationality = data.get('nationality', user.nationality)
    user.language = data.get('language', user.language)
    user.preferred_sailing_areas = data.get('preferred_sailing_areas', user.preferred_sailing_areas)

    db.session.commit()
    return True

def deactivate_dummy_user(user_id):
    user = DummyUser.query.get(user_id)
    if user and user.active:
        user.active = False
        db.session.commit()
        return True
    return False

def get_dummy_user_by_id(user_id):
    return DummyUser.query.filter_by(id=user_id, active=True).first()

def get_all_dummy_users(filter_status='active'):
    """
    Returns dummy users filtered by status:
    - 'active' returns only active users
    - 'inactive' returns only inactive users
    - 'all' returns all users regardless of status
    """
    query = DummyUser.query

    if filter_status == 'active':
        query = query.filter_by(active=True)
    elif filter_status == 'inactive':
        query = query.filter_by(active=False)
    # else 'all' - no filter

    return query.all()

def toggle_dummy_user_active(user_id, set_active=None):
    """
    Toggle or explicitly set the active status of a dummy user.
    If set_active is None, toggles the current status.
    Returns the user object if found, else None.
    """
    user = DummyUser.query.get(user_id)
    if not user:
        return None

    if set_active is None:
        user.active = not user.active
    else:
        user.active = bool(set_active)

    db.session.commit()
    return user
