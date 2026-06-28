"""Tests for the health check and the session-auth endpoints."""


def test_health_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


# --- register --------------------------------------------------------------


def test_register_creates_user(client):
    res = client.post("/register", json={"username": "alice", "password": "secret"})
    assert res.status_code == 201
    assert res.get_json() == {"username": "alice"}


def test_register_requires_username_and_password(client):
    assert client.post("/register", json={"username": "alice"}).status_code == 400
    assert client.post("/register", json={"password": "secret"}).status_code == 400
    assert client.post("/register", json={}).status_code == 400


def test_register_rejects_duplicate_username(client):
    client.post("/register", json={"username": "alice", "password": "secret"})
    res = client.post("/register", json={"username": "alice", "password": "other"})
    assert res.status_code == 409


def test_password_is_not_stored_in_plaintext(client):
    client.post("/register", json={"username": "alice", "password": "secret"})
    import app

    with app.get_db() as db:
        row = db.execute(
            "SELECT password_hash FROM users WHERE username = ?", ("alice",)
        ).fetchone()
    assert row["password_hash"] != "secret"
    assert "secret" not in row["password_hash"]


# --- login -----------------------------------------------------------------


def test_login_with_valid_credentials(client):
    client.post("/register", json={"username": "alice", "password": "secret"})
    res = client.post("/login", json={"username": "alice", "password": "secret"})
    assert res.status_code == 200
    assert res.get_json() == {"username": "alice"}


def test_login_with_wrong_password_is_unauthorized(client):
    client.post("/register", json={"username": "alice", "password": "secret"})
    res = client.post("/login", json={"username": "alice", "password": "wrong"})
    assert res.status_code == 401


def test_login_unknown_user_is_unauthorized(client):
    res = client.post("/login", json={"username": "ghost", "password": "x"})
    assert res.status_code == 401


def test_login_requires_fields(client):
    assert client.post("/login", json={"username": "alice"}).status_code == 400


# --- me / logout -----------------------------------------------------------


def test_me_requires_authentication(client):
    assert client.get("/me").status_code == 401


def test_me_returns_logged_in_user(auth_client):
    res = auth_client.get("/me")
    assert res.status_code == 200
    body = res.get_json()
    assert body["username"] == "alice"
    assert "id" in body


def test_logout_clears_the_session(auth_client):
    assert auth_client.get("/me").status_code == 200
    res = auth_client.post("/logout")
    assert res.status_code == 200
    assert auth_client.get("/me").status_code == 401
