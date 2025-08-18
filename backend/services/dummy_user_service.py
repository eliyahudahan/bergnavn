import re
from backend.models.dummy_user import DummyUser
from backend.config import flags
from backend import db

EMAIL_REGEX = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'

def count_total_dummies():
    """Returns the total number of dummy users (active + inactive)."""
    return DummyUser.query.count()

def count_active_dummies():
    """Returns the number of active dummy users."""
    return DummyUser.query.filter_by(active=True).count()

def create_dummy_user(username, email=None, scenario=None, user_flags=None,
                      gender=None, nationality=None, language=None, preferred_sailing_areas=None):
    """
    Creates a new dummy user with validation:
    - Unique active username and email.
    - Total dummy users (active + inactive) cannot exceed MAX_DUMMY_USERS.
    """
    username = username.strip()
    if not username:
        raise ValueError("Username cannot be empty.")

    # Prevent duplicate active usernames
    if DummyUser.query.filter_by(username=username, active=True).first():
        raise ValueError("Username already exists.")

    # Validate email if provided
    if email:
        email = email.strip()
        if not re.match(EMAIL_REGEX, email):
            raise ValueError("Invalid email format.")
        if DummyUser.query.filter_by(email=email, active=True).first():
            raise ValueError("Email already exists.")

    # Enforce total dummy user limit (active + inactive)
    if count_total_dummies() >= flags.MAX_DUMMY_USERS:
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
    """
    Updates an existing dummy user with validation.
    - Prevents duplicate active usernames/emails.
    """
    user = DummyUser.query.get(user_id)
    if not user:
        return False

    new_username = data.get('username', user.username).strip()
    new_email = data.get('email', user.email)
    new_email = new_email.strip() if new_email else None

    if new_username != user.username:
        if DummyUser.query.filter(
            DummyUser.username == new_username,
            DummyUser.id != user_id,
            DummyUser.active == True
        ).first():
            raise ValueError("Username already exists.")

    if new_email:
        if not re.match(EMAIL_REGEX, new_email):
            raise ValueError("Invalid email format.")
        if new_email != user.email:
            if DummyUser.query.filter(
                DummyUser.email == new_email,
                DummyUser.id != user_id,
                DummyUser.active == True
            ).first():
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
    """Sets a dummy user to inactive if active."""
    user = DummyUser.query.get(user_id)
    if user and user.active:
        user.active = False
        db.session.commit()
        return True
    return False

def get_dummy_user_by_id(user_id):
    """Returns an active dummy user by ID."""
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

    return query.all()

def toggle_dummy_user_active(user_id, set_active=None):
    """
    Toggles or explicitly sets the active status of a dummy user.
    - Always allows toggling active <-> inactive.
    - Does not check total limit (only creation is limited).
    """
    user = DummyUser.query.get(user_id)
    if not user:
        return None

    new_status = not user.active if set_active is None else bool(set_active)

    user.active = new_status
    db.session.commit()
    return user
