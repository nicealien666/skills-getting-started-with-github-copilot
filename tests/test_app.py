from copy import deepcopy

import pytest
import httpx

from src.app import app, activities


INITIAL_ACTIVITIES = deepcopy(activities)


def make_client():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


def reset_activities():
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))


def setup_function():
    reset_activities()


def teardown_function():
    reset_activities()


@pytest.mark.anyio
async def test_root_redirects_to_static_index():
    # Arrange
    async with make_client() as client:
        # Act
        response = await client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code in (307, 308)
        assert response.headers["location"] == "/static/index.html"


@pytest.mark.anyio
async def test_get_activities_returns_activity_catalog():
    # Arrange
    async with make_client() as client:
        # Act
        response = await client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert data["Chess Club"]["participants"] == [
            "michael@mergington.edu",
            "daniel@mergington.edu",
        ]


@pytest.mark.anyio
async def test_signup_adds_participant_to_activity():
    # Arrange
    email = "new.student@mergington.edu"

    async with make_client() as client:
        # Act
        response = await client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Signed up {email} for Chess Club"}
        assert email in activities["Chess Club"]["participants"]


@pytest.mark.anyio
async def test_signup_missing_activity_returns_404():
    # Arrange
    async with make_client() as client:
        # Act
        response = await client.post(
            "/activities/Unknown%20Club/signup",
            params={"email": "student@mergington.edu"},
        )

        # Assert
        assert response.status_code == 404
        assert response.json() == {"detail": "Activity not found"}


@pytest.mark.anyio
async def test_unregister_removes_participant_from_activity():
    # Arrange
    email = "michael@mergington.edu"

    async with make_client() as client:
        # Act
        response = await client.delete(
            "/activities/Chess%20Club/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
        assert email not in activities["Chess Club"]["participants"]


@pytest.mark.anyio
async def test_unregister_missing_participant_returns_404():
    # Arrange
    async with make_client() as client:
        # Act
        response = await client.delete(
            "/activities/Chess%20Club/signup",
            params={"email": "missing@mergington.edu"},
        )

        # Assert
        assert response.status_code == 404
        assert response.json() == {"detail": "Participant not found"}


@pytest.mark.anyio
async def test_unregister_missing_activity_returns_404():
    # Arrange
    async with make_client() as client:
        # Act
        response = await client.delete(
            "/activities/Unknown%20Club/signup",
            params={"email": "student@mergington.edu"},
        )

        # Assert
        assert response.status_code == 404
        assert response.json() == {"detail": "Activity not found"}