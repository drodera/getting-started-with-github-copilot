import copy
from urllib.parse import quote

from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)

ORIGINAL_ACTIVITIES = copy.deepcopy(activities)


def setup_function():
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))


def test_get_activities_returns_all_activities():
    # Arrange
    # (activities already set up via setup_function)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert data["Chess Club"]["description"].startswith("Learn strategies")
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_adds_participant():
    # Arrange
    email = "newstudent@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = client.post(f"/activities/{quote(activity_name)}/signup?email={quote(email)}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    activity_data = client.get("/activities").json()[activity_name]
    assert email in activity_data["participants"]


def test_signup_duplicate_returns_400():
    # Arrange
    email = "duplicate@mergington.edu"
    activity_name = "Yoga Club"
    activities[activity_name] = {
        "description": "Relax and stretch.",
        "schedule": "Fridays, 4:00 PM",
        "max_participants": 10,
        "participants": [],
    }

    # Act
    first_response = client.post(f"/activities/{quote(activity_name)}/signup?email={quote(email)}")
    second_response = client.post(f"/activities/{quote(activity_name)}/signup?email={quote(email)}")

    # Assert
    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Student already signed up for this activity"


def test_remove_participant_deletes_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "removeme@mergington.edu"
    signup_response = client.post(f"/activities/{quote(activity_name)}/signup?email={quote(email)}")
    assert signup_response.status_code == 200

    # Act
    delete_response = client.delete(
        f"/activities/{quote(activity_name)}/participants?email={quote(email)}"
    )

    # Assert
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == f"Unregistered {email} from {activity_name}"
    activity_data = client.get("/activities").json()[activity_name]
    assert email not in activity_data["participants"]


def test_remove_nonexistent_participant_returns_404():
    # Arrange
    activity_name = "Chess Club"
    email = "missing@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/participants?email={quote(email)}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
