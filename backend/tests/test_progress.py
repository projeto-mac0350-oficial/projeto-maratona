"""Tests for the per-user study-progress endpoints."""

import app

ITEM = {
    "item_key": "busca_binaria:prob:roadworks",
    "kind": "problem",
    "label": "Problema 1 - Roadworks",
    "done": True,
}


# --- auth gating -----------------------------------------------------------


def test_get_progress_requires_authentication(client):
    assert client.get("/progress").status_code == 401


def test_post_progress_requires_authentication(client):
    assert client.post("/progress", json=ITEM).status_code == 401


# --- reading ---------------------------------------------------------------


def test_progress_starts_empty(auth_client):
    res = auth_client.get("/progress")
    assert res.status_code == 200
    assert res.get_json() == {}


# --- writing ---------------------------------------------------------------


def test_post_progress_saves_and_is_returned(auth_client):
    res = auth_client.post("/progress", json=ITEM)
    assert res.status_code == 200
    assert res.get_json() == {"item_key": ITEM["item_key"], "done": True}

    saved = auth_client.get("/progress").get_json()
    assert saved == {
        ITEM["item_key"]: {
            "done": True,
            "kind": "problem",
            "label": "Problema 1 - Roadworks",
        }
    }


def test_post_progress_requires_item_key_and_kind(auth_client):
    assert auth_client.post("/progress", json={"kind": "problem"}).status_code == 400
    assert (
        auth_client.post("/progress", json={"item_key": "k"}).status_code == 400
    )


def test_post_progress_upserts_in_place(auth_client):
    auth_client.post("/progress", json=ITEM)
    # toggle the same item back to not-done
    res = auth_client.post("/progress", json={**ITEM, "done": False})
    assert res.get_json() == {"item_key": ITEM["item_key"], "done": False}

    saved = auth_client.get("/progress").get_json()
    assert list(saved.keys()) == [ITEM["item_key"]]  # no duplicate row
    assert saved[ITEM["item_key"]]["done"] is False


def test_missing_done_defaults_to_false(auth_client):
    payload = {"item_key": "k", "kind": "ref", "label": "L"}  # no "done"
    res = auth_client.post("/progress", json=payload)
    assert res.get_json()["done"] is False


# --- isolation -------------------------------------------------------------


def test_progress_is_per_user(client):
    # user A saves an item
    client.post("/register", json={"username": "a", "password": "x"})
    client.post("/login", json={"username": "a", "password": "x"})
    client.post("/progress", json=ITEM)

    # user B (separate cookie jar) sees nothing
    other = app.app.test_client()
    other.post("/register", json={"username": "b", "password": "x"})
    other.post("/login", json={"username": "b", "password": "x"})
    assert other.get("/progress").get_json() == {}

    # user A still sees their item
    assert ITEM["item_key"] in client.get("/progress").get_json()
