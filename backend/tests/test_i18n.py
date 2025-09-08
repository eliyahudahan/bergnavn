from backend.utils.translations import TRANSLATIONS
from app import create_app
import pytest

@pytest.fixture(scope="session")
def app():
    app = create_app(testing=True)
    return app

def test_translations_keys_mirror():
    en = TRANSLATIONS["en"]
    no = TRANSLATIONS["no"]
    assert set(en.keys()) == set(no.keys())
    for section in en.keys():
        assert set(en[section].keys()) == set(no[section].keys())

def test_cruises_view_no_does_not_show_built_in_title(app):
    with app.test_client() as c:
        resp = c.get("/cruises/view?lang=no")
        txt = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "<built-in method title" not in txt.lower()
