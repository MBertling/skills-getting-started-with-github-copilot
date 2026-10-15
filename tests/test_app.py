import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activities(monkeypatch):
    test_activities = {
        "Chess Club": {
            "description": "Learn chess strategies",
            "schedule": "Fridays, 3:30 PM",
            "max_participants": 2,
            "participants": ["existing@mergington.edu"],
        }
    }
    monkeypatch.setattr(app_module, "activities", test_activities)
    return test_activities


@pytest.fixture
def client(activities):
    return TestClient(app_module.app)


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_participants = ["existing@mergington.edu"]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == expected_participants


def test_signup_adds_participant_and_is_visible_in_activities(client):
    # Arrange
    email = "new-student@mergington.edu"

    # Act
    signup_response = client.post(
        "/activities/Chess%20Club/signup", params={"email": email}
    )
    activities_response = client.get("/activities")

    # Assert
    assert signup_response.status_code == 200
    assert signup_response.json() == {
        "message": f"Signed up {email} for Chess Club"
    }
    assert email in activities_response.json()["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    email = "existing@mergington.edu"

    # Act
    response = client.post(
        "/activities/Chess%20Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_unknown_activity(client):
    # Arrange
    email = "new-student@mergington.edu"

    # Act
    response = client.post(
        "/activities/Unknown%20Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_requires_email(client):
    # Arrange
    url = "/activities/Chess%20Club/signup"

    # Act
    response = client.post(url)

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "email"]


def test_unregister_removes_participant_and_updates_activities(client):
    # Arrange
    email = "existing@mergington.edu"

    # Act
    unregister_response = client.delete(
        "/activities/Chess%20Club/signup", params={"email": email}
    )
    activities_response = client.get("/activities")

    # Assert
    assert unregister_response.status_code == 200
    assert unregister_response.json() == {
        "message": f"Removed {email} from Chess Club"
    }
    assert email not in activities_response.json()["Chess Club"]["participants"]


def test_unregister_rejects_missing_participant(client):
    # Arrange
    email = "missing@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Chess%20Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    email = "new-student@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Unknown%20Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_root_redirects_to_static_page(client):
    # Arrange
    url = "/"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"