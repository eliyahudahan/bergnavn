from backend.models.dummy_user import DummyUser
from backend.config import flags
from backend import db

# ✅ יצירת משתמש דמה
def create_dummy_user(username, email=None, scenario=None, user_flags=None,
                      gender=None, nationality=None, language=None, preferred_sailing_areas=None):

    current_count = DummyUser.query.filter_by(active=True).count()
    if current_count >= flags.MAX_DUMMY_USERS:
        raise ValueError(f"Exceeded maximum allowed dummy users ({flags.MAX_DUMMY_USERS})")

    user = DummyUser(
        username=username,
        email=email,
        scenario=scenario,
        flags=user_flags or {},  # ← פתרון בטוח ל־None
        gender=gender,
        nationality=nationality,
        language=language,
        preferred_sailing_areas=preferred_sailing_areas
    )

    db.session.add(user)
    db.session.commit()
    return user

# ✅ עדכון משתמש קיים
def update_dummy_user(user_id, data):
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

# ✅ מחיקה לוגית (deactivate)
def deactivate_dummy_user(user_id):
    user = DummyUser.query.get(user_id)
    if user and user.active:
        user.active = False
        db.session.commit()
        return True
    return False

# ✅ שליפת כל המשתמשים הפעילים (אפשר גם להוסיף סינון בעתיד)
def get_all_dummy_users():
    return DummyUser.query.filter_by(active=True).all()

# ✅ שליפת משתמש בודד לפי מזהה
def get_dummy_user_by_id(user_id):
    user = DummyUser.query.get(user_id)
    if user and user.active:
        return user
    return None

