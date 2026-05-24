import pytest


class TestCreateWorkout:
    def test_create_persists_workout_name_and_workout_date(
        self, client, token_headers, sample_workout_data
    ):
        resp = client.post(
            "/api/workouts",
            json={
                **sample_workout_data,
                "workout_name": "  Sunset Steady State  ",
                "workout_date": "2026-05-18T12:00:00",
            },
            headers=token_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["workout_name"] == "Sunset Steady State"
        assert body["workout_date"].startswith("2026-05-18T12:00:00")

    def test_authenticated_create_returns_201_and_source_manual(
        self, client, token_headers, sample_workout_data
    ):
        resp = client.post("/api/workouts", json=sample_workout_data, headers=token_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["source"] == "manual"
        assert body["duration_seconds"] == 1800
        assert body["distance_meters"] == 5000.0

    def test_avg_split_500m_is_computed(
        self, client, token_headers, sample_workout_data
    ):
        resp = client.post("/api/workouts", json=sample_workout_data, headers=token_headers)
        assert resp.status_code == 201
        body = resp.json()
        expected = (1800 / 5000.0) * 500
        assert body["avg_split_500m"] == pytest.approx(expected, rel=1e-6)

    def test_missing_auth_is_rejected(self, client, sample_workout_data):
        resp = client.post("/api/workouts", json=sample_workout_data)
        assert resp.status_code in (401, 403)

    def test_invalid_duration_returns_422(self, client, token_headers):
        resp = client.post("/api/workouts", json={"duration_seconds": -1, "distance_meters": 5000}, headers=token_headers)
        assert resp.status_code == 422

    def test_invalid_distance_returns_422(self, client, token_headers):
        resp = client.post("/api/workouts", json={"duration_seconds": 1800, "distance_meters": -1}, headers=token_headers)
        assert resp.status_code == 422

    def test_zero_duration_returns_422(self, client, token_headers):
        resp = client.post("/api/workouts", json={"duration_seconds": 0, "distance_meters": 5000}, headers=token_headers)
        assert resp.status_code == 422

    def test_zero_distance_returns_422(self, client, token_headers):
        resp = client.post("/api/workouts", json={"duration_seconds": 1800, "distance_meters": 0}, headers=token_headers)
        assert resp.status_code == 422

    def test_omitted_visibility_defaults_private(
        self, client, token_headers, sample_workout_data
    ):
        resp = client.post("/api/workouts", json=sample_workout_data, headers=token_headers)
        assert resp.status_code == 201
        assert resp.json()["visibility"] == "private"

    def test_team_visibility_requires_team_id(
        self, client, token_headers_no_team, sample_workout_data
    ):
        data = {**sample_workout_data, "visibility": "team"}
        resp = client.post("/api/workouts", json=data, headers=token_headers_no_team)
        assert resp.status_code in (400, 403)
        assert "team" in resp.json()["detail"].lower()

    def test_team_visibility_rejected_when_not_member_of_team(
        self, client, token_headers_no_team, team, sample_workout_data
    ):
        data = {**sample_workout_data, "visibility": "team", "team_id": str(team.id)}
        resp = client.post("/api/workouts", json=data, headers=token_headers_no_team)
        assert resp.status_code in (400, 403)
        assert "team" in resp.json()["detail"].lower()

    def test_team_visibility_allowed_when_on_team(
        self, client, token_headers, team, sample_workout_data
    ):
        data = {**sample_workout_data, "visibility": "team", "team_id": str(team.id)}
        resp = client.post("/api/workouts", json=data, headers=token_headers)
        assert resp.status_code == 201
        assert resp.json()["visibility"] == "team"
        assert resp.json()["team_id"] == str(team.id)

    def test_workout_date_defaults_to_now(
        self, client, token_headers, sample_workout_data
    ):
        resp = client.post("/api/workouts", json=sample_workout_data, headers=token_headers)
        assert resp.status_code == 201
        assert resp.json()["workout_date"] is not None

    def test_long_workout_name_returns_422(self, client, token_headers, sample_workout_data):
        resp = client.post(
            "/api/workouts",
            json={**sample_workout_data, "workout_name": "x" * 121},
            headers=token_headers,
        )
        assert resp.status_code == 422

    def test_source_and_user_id_set_server_side(
        self, client, token_headers, user_on_team, sample_workout_data
    ):
        resp = client.post("/api/workouts", json=sample_workout_data, headers=token_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["source"] == "manual"
        assert body["user_id"] == str(user_on_team.id)
        assert body["source_id"] is None


class TestListWorkouts:
    def test_list_returns_only_current_user_workouts(
        self, client, db, user_on_team, user_no_team, sample_workout_data
    ):
        token = token_headers(user_on_team)
        resp = client.post("/api/workouts", json=sample_workout_data, headers=token)
        assert resp.status_code == 201

        token_no = token_headers(user_no_team)
        resp2 = client.get("/api/workouts", headers=token_no)
        assert resp2.status_code == 200
        assert resp2.json() == {"workouts": []}

        resp3 = client.get("/api/workouts", headers=token)
        assert resp3.status_code == 200
        assert len(resp3.json()["workouts"]) == 1

    def test_list_returns_workouts_key(
        self, client, token_headers, sample_workout_data
    ):
        resp = client.get("/api/workouts", headers=token_headers)
        assert resp.status_code == 200
        assert "workouts" in resp.json()


class TestWorkoutDetail:
    def test_get_workout_returns_owned_workout(
        self, client, token_headers, sample_workout_data
    ):
        created = client.post("/api/workouts", json=sample_workout_data, headers=token_headers)
        assert created.status_code == 201

        workout_id = created.json()["id"]
        resp = client.get(f"/api/workouts/{workout_id}", headers=token_headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == workout_id
        assert body["distance_meters"] == sample_workout_data["distance_meters"]

    def test_get_workout_hides_non_owned_workout(
        self, client, user_on_team, user_no_team, sample_workout_data
    ):
        owner_headers = token_headers(user_on_team)
        intruder_headers = token_headers(user_no_team)
        created = client.post("/api/workouts", json=sample_workout_data, headers=owner_headers)
        assert created.status_code == 201

        workout_id = created.json()["id"]
        resp = client.get(f"/api/workouts/{workout_id}", headers=intruder_headers)

        assert resp.status_code == 404


class TestUpdateWorkout:
    def test_patch_updates_workout_name_and_workout_date(
        self, client, token_headers, sample_workout_data
    ):
        created = client.post("/api/workouts", json=sample_workout_data, headers=token_headers)
        assert created.status_code == 201

        workout_id = created.json()["id"]
        resp = client.patch(
            f"/api/workouts/{workout_id}",
            json={
                "workout_name": "  Piece 4 x 1k  ",
                "workout_date": "2026-05-17T12:00:00",
            },
            headers=token_headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["workout_name"] == "Piece 4 x 1k"
        assert body["workout_date"].startswith("2026-05-17T12:00:00")

    def test_patch_null_workout_name_clears_it(
        self, client, token_headers, sample_workout_data
    ):
        created = client.post(
            "/api/workouts",
            json={**sample_workout_data, "workout_name": "Morning Row"},
            headers=token_headers,
        )
        assert created.status_code == 201

        workout_id = created.json()["id"]
        resp = client.patch(
            f"/api/workouts/{workout_id}",
            json={"workout_name": None},
            headers=token_headers,
        )

        assert resp.status_code == 200
        assert resp.json()["workout_name"] is None

    def test_patch_updates_workout_and_recomputes_split(
        self, client, token_headers, sample_workout_data
    ):
        created = client.post("/api/workouts", json=sample_workout_data, headers=token_headers)
        assert created.status_code == 201

        workout_id = created.json()["id"]
        payload = {
            "duration_seconds": 1500,
            "distance_meters": 6000,
            "notes": "Updated notes",
        }
        resp = client.patch(f"/api/workouts/{workout_id}", json=payload, headers=token_headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["duration_seconds"] == 1500
        assert body["distance_meters"] == 6000
        assert body["notes"] == "Updated notes"
        assert body["avg_split_500m"] == pytest.approx((1500 / 6000) * 500, rel=1e-6)

    def test_patch_private_visibility_clears_team_id(
        self, client, token_headers, team, sample_workout_data
    ):
        created = client.post(
            "/api/workouts",
            json={**sample_workout_data, "visibility": "team", "team_id": str(team.id)},
            headers=token_headers,
        )
        assert created.status_code == 201

        workout_id = created.json()["id"]
        resp = client.patch(
            f"/api/workouts/{workout_id}",
            json={"visibility": "private"},
            headers=token_headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["visibility"] == "private"
        assert body["team_id"] is None

    def test_patch_team_visibility_requires_active_membership(
        self, client, token_headers_no_team, team, sample_workout_data
    ):
        created = client.post("/api/workouts", json=sample_workout_data, headers=token_headers_no_team)
        assert created.status_code == 201

        workout_id = created.json()["id"]
        resp = client.patch(
            f"/api/workouts/{workout_id}",
            json={"visibility": "team", "team_id": str(team.id)},
            headers=token_headers_no_team,
        )

        assert resp.status_code in (400, 403)
        assert "team" in resp.json()["detail"].lower()

    def test_patch_rejects_null_required_fields(
        self, client, token_headers, sample_workout_data
    ):
        created = client.post("/api/workouts", json=sample_workout_data, headers=token_headers)
        assert created.status_code == 201

        workout_id = created.json()["id"]
        resp = client.patch(
            f"/api/workouts/{workout_id}",
            json={"workout_date": None},
            headers=token_headers,
        )

        assert resp.status_code == 422

    def test_patch_rejects_null_visibility(
        self, client, token_headers, sample_workout_data
    ):
        created = client.post("/api/workouts", json=sample_workout_data, headers=token_headers)
        assert created.status_code == 201

        workout_id = created.json()["id"]
        resp = client.patch(
            f"/api/workouts/{workout_id}",
            json={"visibility": None},
            headers=token_headers,
        )

        assert resp.status_code == 422

    def test_patch_hides_non_owned_workout(
        self, client, user_on_team, user_no_team, sample_workout_data
    ):
        owner_headers = token_headers(user_on_team)
        intruder_headers = token_headers(user_no_team)
        created = client.post("/api/workouts", json=sample_workout_data, headers=owner_headers)
        assert created.status_code == 201

        workout_id = created.json()["id"]
        resp = client.patch(
            f"/api/workouts/{workout_id}",
            json={"notes": "Nope"},
            headers=intruder_headers,
        )

        assert resp.status_code == 404


class TestDeleteWorkout:
    def test_delete_removes_owned_workout(
        self, client, token_headers, sample_workout_data
    ):
        created = client.post("/api/workouts", json=sample_workout_data, headers=token_headers)
        assert created.status_code == 201

        workout_id = created.json()["id"]
        resp = client.delete(f"/api/workouts/{workout_id}", headers=token_headers)

        assert resp.status_code == 204

        follow_up = client.get(f"/api/workouts/{workout_id}", headers=token_headers)
        assert follow_up.status_code == 404

    def test_delete_hides_non_owned_workout(
        self, client, user_on_team, user_no_team, sample_workout_data
    ):
        owner_headers = token_headers(user_on_team)
        intruder_headers = token_headers(user_no_team)
        created = client.post("/api/workouts", json=sample_workout_data, headers=owner_headers)
        assert created.status_code == 201

        workout_id = created.json()["id"]
        resp = client.delete(f"/api/workouts/{workout_id}", headers=intruder_headers)

        assert resp.status_code == 404


def token_headers(user):
    from app.services.auth import create_access_token
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}
