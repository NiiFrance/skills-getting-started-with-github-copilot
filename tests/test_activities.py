import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities database before each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


client = TestClient(app)


# ── GET / ─────────────────────────────────────────────

class TestRootRedirect:
    def test_redirects_to_index(self):
        # Arrange
        url = "/"

        # Act
        response = client.get(url, follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


# ── GET /activities ───────────────────────────────────

class TestGetActivities:
    def test_returns_all_activities(self):
        # Arrange
        expected_activities = {
            "Chess Club", "Programming Class", "Gym Class",
            "Soccer Team", "Basketball Club", "Drama Club",
            "Art Workshop", "Math Olympiad", "Science Club",
        }

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == expected_activities

    def test_activity_has_required_fields(self):
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        for name, details in data.items():
            assert required_fields.issubset(details.keys()), f"{name} missing fields"


# ── POST /activities/{name}/signup ────────────────────

class TestSignup:
    def test_signup_success(self):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        assert email in activities[activity_name]["participants"]

    def test_signup_duplicate_returns_400(self):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # already registered

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ── DELETE /activities/{name}/signup ──────────────────

class TestUnregister:
    def test_unregister_success(self):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # currently registered

        # Act
        response = client.request(
            "DELETE",
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        assert email not in activities[activity_name]["participants"]

    def test_unregister_not_signed_up_returns_404(self):
        # Arrange
        activity_name = "Chess Club"
        email = "nobody@mergington.edu"

        # Act
        response = client.request(
            "DELETE",
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_nonexistent_activity_returns_404(self):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.request(
            "DELETE",
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
