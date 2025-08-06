from backend.models.dummy_user import DummyUser
from backend.config import flags
from backend import db

# ✅ Create a new dummy user
def create_dummy_user(username, email=None, scenario=None, user_flags=None,
                      gender=None, nationality=None, language=None, preferred_sailing_areas=None):
    """
    Creates a dummy user with provided details.
    No password handling here as dummy users do not require authentication.
    Enforces maximum number of active dummy users.
    """
    current_count = DummyUser.query.filter_by(active=True).count()
    if current_count >= flags.MAX_DUMMY_USERS:
        raise ValueError(f"Exceeded maximum allowed dummy users ({flags.MAX_DUMMY_USERS})")

    user = DummyUser(
        username=username,
        email=email,
        scenario=scenario,
        flags=user_flags or {},  # Safe default if None
        gender=gender,
        nationality=nationality,
        language=language,
        preferred_sailing_areas=preferred_sailing_areas,
        active=True  # Ensure user is active when created
    )

    db.session.add(user)
    db.session.commit()
    return user

# ✅ Update existing dummy user
def update_dummy_user(user_id, data):
    """
    Updates fields of an active dummy user.
    Ignores password updates as dummy users do not have passwords.
    Returns True if update succeeded, False otherwise.
    """
    user = DummyUser.query.get(user_id)
    if not user or not user.active:
        return False

    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    user.scenario = data.get('scenario', user.scenario)
    user.flags = data.get('flags', user.flags)
    user.gender = data.get('gender', user.gender)
    user.nationality = data.get('nationality', user.nationality)
    user.language = data.get('language', user.language)
    user.preferred_sailing_areas = data.get('preferred_sailing_areas', user.preferred_sailing_areas)

    db.session.commit()
    return True

# ✅ Soft-delete (deactivate) a dummy user
def deactivate_dummy_user(user_id):
    """
    Marks a dummy user as inactive without removing from database.
    Returns True if deactivation succeeded, False otherwise.
    """
    user = DummyUser.query.get(user_id)
    if user and user.active:
        user.active = False
        db.session.commit()
        return True
    return False

# ✅ Retrieve all active dummy users
def get_all_dummy_users():
    """
    Returns a list of all active dummy users.
    """
    return DummyUser.query.filter_by(active=True).all()

# ✅ Retrieve a single active dummy user by ID
def get_dummy_user_by_id(user_id):
    """
    Returns the dummy user if active, else None.
    """
    user = DummyUser.query.get(user_id)
    if user and user.active:
        return user
    return None


