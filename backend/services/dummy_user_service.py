import re
from backend.models.dummy_user import DummyUser
from backend.config import flags
from backend import db
from backend.utils.translations import translate

EMAIL_REGEX = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'

def count_total_dummies():
    """Returns the total number of dummy users (active + inactive)."""
    return DummyUser.query.count()

def count_active_dummies():
    """Returns the number of active dummy users."""
    return DummyUser.query.filter_by(active=True).count()

def create_dummy_user(username, email=None, scenario=None, user_flags=None,
                      gender=None, nationality=None, language=None, preferred_sailing_areas=None, lang='en'):
    """
    Creates a new dummy user with validation:
    - Unique active username and email.
    - Total dummy users (active + inactive) cannot exceed MAX_DUMMY_USERS.
    - Returns the created user.
    """
    username = username.strip()
    if not username:
        raise ValueError(translate('username_required', lang, section='dummy_users'))

    if DummyUser.query.filter_by(username=username, active=True).first():
        raise ValueError(translate('username_exists', lang, section='dummy_users'))

    if email:
        email = email.strip()
        if not re.match(EMAIL_REGEX, email):
            raise ValueError(translate('invalid_email', lang, section='dummy_users'))
        if DummyUser.query.filter_by(email=email, active=True).first():
            raise ValueError(translate('email_exists', lang, section='dummy_users'))

    if count_total_dummies() >= flags.MAX_DUMMY_USERS:
        raise ValueError(translate('limit_dummy', lang, section='dummy_users'))

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

def update_dummy_user(user_id, data, lang='en'):
    """
    Updates an existing dummy user with validation.
    - Prevents duplicate active usernames/emails.
    """
    user = DummyUser.query.get(user_id)
    if not user:
        raise ValueError(translate('user_not_found', lang, section='dummy_users'))

    new_username = data.get('username', user.username).strip()
    new_email = data.get('email', user.email)
    new_email = new_email.strip() if new_email else None

    if new_username != user.username:
        if DummyUser.query.filter(
            DummyUser.username == new_username,
            DummyUser.id != user_id,
            DummyUser.active == True
        ).first():
            raise ValueError(translate('username_exists', lang, section='dummy_users'))

    if new_email:
        if not re.match(EMAIL_REGEX, new_email):
            raise ValueError(translate('invalid_email', lang, section='dummy_users'))
        if new_email != user.email:
            if DummyUser.query.filter(
                DummyUser.email == new_email,
                DummyUser.id != user_id,
                DummyUser.active == True
            ).first():
                raise ValueError(translate('email_exists', lang, section='dummy_users'))

    user.username = new_username
    user.email = new_email
    user.scenario = data.get('scenario', user.scenario)
    user.flags = data.get('flags', user.flags)
    user.gender = data.get('gender', user.gender)
    user.nationality = data.get('nationality', user.nationality)
    user.language = data.get('language', user.language)
    user.preferred_sailing_areas = data.get('preferred_sailing_areas', user.preferred_sailing_areas)

    db.session.commit()
    return user

def deactivate_dummy_user(user_id, lang='en'):
    """Sets a dummy user to inactive if active."""
    user = DummyUser.query.get(user_id)
    if user and user.active:
        user.active = False
        db.session.commit()
        return user
    raise ValueError(translate('user_not_found', lang, section='dummy_users'))

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

def toggle_dummy_user_active(user_id, set_active=None, lang='en'):
    """
    Toggles or explicitly sets the active status of a dummy user.
    """
    user = DummyUser.query.get(user_id)
    if not user:
        raise ValueError(translate('user_not_found', lang, section='dummy_users'))

    user.active = not user.active if set_active is None else bool(set_active)
    db.session.commit()
    return user
