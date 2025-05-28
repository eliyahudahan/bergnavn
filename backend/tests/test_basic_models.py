# backend/tests/test_basic_models.py

import sys
import os
# מוסיפים את השורש של הפרויקט ל־PYTHONPATH כדי שנוכל לייבא את create_app מ־app.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest

# מייבאים מהשורש את הפונקציה ליצירת האפליקציה
from app import create_app
from backend.models.port import Port
from backend import db

@pytest.fixture(scope='module')
def test_app():
    """
    יוצר אפליקציית Flask במצב 'testing' ודוחף CONTEXT.
    """
    app = create_app('testing')
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

@pytest.fixture(scope='module')
def init_database(test_app):
    """
    מריץ db.create_all() בתוך ה־application context,
    ומנקה בסיום.
    """
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()

def test_create_port(init_database):
    """
    smoke test פשוט ל־Port model:
    יצירה, שמירה ושליפה.
    """
    # יצירת מופע חדש
    port = Port(name='Copenhagen', country='Denmark')
    db.session.add(port)
    db.session.commit()

    # שליפה ובדיקת הערכים
    saved = Port.query.filter_by(name='Copenhagen').first()
    assert saved is not None
    assert saved.country == 'Denmark'
