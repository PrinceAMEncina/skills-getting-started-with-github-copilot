import copy
import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


# Load the app module directly to avoid package import issues
app_path = Path(__file__).resolve().parents[1] / "src" / "app.py"
spec = importlib.util.spec_from_file_location("app_module", str(app_path))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

client = TestClient(app_module.app)


# Keep an original copy of activities and restore before each test
_ORIGINAL_ACTIVITIES = copy.deepcopy(app_module.activities)


def _reset_activities():
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(_ORIGINAL_ACTIVITIES))


def setup_function(function):
    _reset_activities()


def teardown_function(function):
    _reset_activities()


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert "Baseball Team" in data
    assert isinstance(data["Baseball Team"]["participants"], list)


def test_signup_and_prevent_duplicate():
    email = "tester@example.edu"
    activity = "Baseball Team"

    # sign up
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200
    assert email in app_module.activities[activity]["participants"]

    # duplicate signup should fail
    resp2 = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp2.status_code == 400


def test_remove_participant():
    activity = "Music Ensemble"
    email = "lucas@mergington.edu"

    assert email in app_module.activities[activity]["participants"]

    resp = client.delete(f"/activities/{activity}/participants?email={email}")
    assert resp.status_code == 200
    assert email not in app_module.activities[activity]["participants"]

    # removing again should return 404
    resp2 = client.delete(f"/activities/{activity}/participants?email={email}")
    assert resp2.status_code == 404
