"""Tests for the heatmap endpoint"""

import app as flask_app
from datetime import date, timedelta

def test_heatmap_requires_authentication(client):
    assert client.get("/heatmap").status_code == 401

def test_heatmap_starts_empty(auth_client):
    res = auth_client.get("/heatmap")
    assert res.status_code == 200
    data = res.get_json()
    assert data["today"]
    assert data["counts"] == {}

def test_heatmap_counts_completed_progress(auth_client):
    auth_client.post("/progress",json={"item_key": "busca_binaria:prob:roadworks","kind": "problem","label": "Problema 1 - Roadworks","done": True,},)
    res = auth_client.get("/heatmap")
    data = res.get_json()
    today = data["today"]
    assert data["counts"][today] == 1

def test_heatmap_ignores_not_done_progress(auth_client):
    auth_client.post("/progress",json={"item_key": "busca_binaria:prob:roadworks", "kind": "problem","label": "Problema 1 - Roadworks","done": False,},)
    data = auth_client.get("/heatmap").get_json()
    assert data["counts"] == {}

def test_heatmap_is_per_user(auth_client):
    auth_client.post("/progress", json={"item_key": "topic:ref:item1","kind": "ref","label": "Reference","done": True})
    other = flask_app.app.test_client()
    other.post("/register", json={"username": "bob","password": "123"})
    other.post("/login", json={"username": "bob","password": "123"})
    response = other.get("/heatmap")
    assert response.get_json()["counts"] == {}

def test_heatmap_multiple_days(auth_client):

    with flask_app.get_db() as db:
        user_id = db.execute(
            "SELECT id FROM users WHERE username = 'alice'"
        ).fetchone()["id"]

        yesterday = (date.today() - timedelta(days=1)).isoformat()
        two_days_ago = (date.today() - timedelta(days=2)).isoformat()

        db.execute(
            """
            INSERT INTO progress
            (user_id, item_key, kind, label, done, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                "item1",
                "problem",
                "Problema 1",
                1,
                yesterday + " 10:00:00",
            ),
        )

        db.execute(
            """
            INSERT INTO progress
            (user_id, item_key, kind, label, done, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                "item2",
                "problem",
                "Problema 2",
                1,
                two_days_ago + " 10:00:00",
            ),
        )

        db.commit()

    data = auth_client.get("/heatmap").get_json()
    assert data["counts"] == {yesterday: 1,two_days_ago: 1,}

def test_heatmap_counts_same_day(auth_client):
    auth_client.post("/progress",json={"item_key": "item1","kind": "problem","label": "Problema 1","done": True})
    auth_client.post("/progress",json={"item_key": "item2","kind": "problem","label": "Problema 2","done": True})
    data = auth_client.get("/heatmap").get_json()
    assert data["counts"][data["today"]] == 2

def test_heatmap_removes_unchecked_progress(auth_client):
    auth_client.post("/progress", json={"item_key": "topic:ref:item1","kind": "ref","label": "Reference","done": True})
    auth_client.post("/progress", json={"item_key": "topic:ref:item1","kind": "ref","label": "Reference","done": False})
    response = auth_client.get("/heatmap")
    assert response.get_json()["counts"] == {}