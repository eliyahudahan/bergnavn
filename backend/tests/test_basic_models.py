import pytest
from backend.models.port import Port
from backend import create_app, db

@pytest.fixture(scope='module')
def test_client():
    app = create_app('testing')  # נניח שהגדרת קונפיג מיוחד ל-testing
    testing_client = app.test_client()
    
    # Setup context
    ctx = app.app_context()
    ctx.push()

    yield testing_client  # this is where the testing happens!

    ctx.pop()

@pytest.fixture(scope='module')
def init_database():
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()

def test_create_port(init_database):
    # יצירת מופע חדש
    port = Port(name='Copenhagen', country='Denmark')
    db.session.add(port)
    db.session.commit()

    # שליפה
    saved_port = Port.query.filter_by(name='Copenhagen').first()
    assert saved_port is not None
    assert saved_port.country == 'Denmark'
