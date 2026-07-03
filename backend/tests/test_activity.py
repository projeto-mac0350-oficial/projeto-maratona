"""Tests for login-day recording and the /activity endpoint.

A "login day" is any day the user was seen authenticated: successful POST
/login, GET /me (hit by the auth widget on every page load) and GET /activity
all record it. /activity returns the current month's days plus the streak of
consecutive days ending today.
"""

from datetime import date, timedelta

import app


def iso_days_ago(n):
    return (date.today() - timedelta(days=n)).isoformat()


def seed_days(days):
    """Insert login-day rows for alice (the auth_client user) directly."""
    with app.get_db() as db:
        uid = db.execute(
            "SELECT id FROM users WHERE username = 'alice'"
        ).fetchone()["id"]
        db.executemany(
            "INSERT OR IGNORE INTO login_days (user_id, day) VALUES (?, ?)",
            [(uid, d) for d in days],
        )


def clear_days():
    with app.get_db() as db:
        db.execute("DELETE FROM login_days")


def recorded_days(username="alice"):
    with app.get_db() as db:
        rows = db.execute(
            "SELECT day FROM login_days JOIN users ON users.id = user_id"
            " WHERE username = ? ORDER BY day",
            (username,),
        ).fetchall()
    return [row["day"] for row in rows]


# --- auth gating -------------------------------------------------------------


def test_activity_requires_authentication(client):
    assert client.get("/activity").status_code == 401


# --- recording ---------------------------------------------------------------


def test_login_records_today(client):
    client.post("/register", json={"username": "alice", "password": "secret"})
    client.post("/login", json={"username": "alice", "password": "secret"})
    assert recorded_days() == [date.today().isoformat()]


def test_me_records_today(auth_client):
    clear_days()  # drop the row recorded by the fixture's login
    auth_client.get("/me")
    assert recorded_days() == [date.today().isoformat()]


def test_duplicate_recording_is_idempotent(auth_client):
    auth_client.get("/activity")
    auth_client.get("/activity")
    auth_client.post("/login", json={"username": "alice", "password": "secret"})
    assert recorded_days() == [date.today().isoformat()]


# --- /activity ---------------------------------------------------------------


def test_activity_self_records_and_shape(auth_client):
    clear_days()
    res = auth_client.get("/activity")
    today = date.today().isoformat()
    assert res.status_code == 200
    assert res.get_json() == {"today": today, "streak": 1, "days": [today]}


def test_streak_counts_consecutive_days(auth_client):
    seed_days([iso_days_ago(1), iso_days_ago(2)])
    data = auth_client.get("/activity").get_json()
    assert data["streak"] == 3
    assert date.today().isoformat() in data["days"]


def test_gap_resets_streak(auth_client):
    seed_days([iso_days_ago(2), iso_days_ago(3)])
    data = auth_client.get("/activity").get_json()
    assert data["streak"] == 1


def test_days_lists_only_current_month(auth_client):
    old = iso_days_ago(40)  # longer than any month, so always a past month
    seed_days([old])
    data = auth_client.get("/activity").get_json()
    assert old not in data["days"]
    assert date.today().isoformat() in data["days"]


# --- isolation ---------------------------------------------------------------


def test_activity_is_per_user(auth_client):
    seed_days([iso_days_ago(1), iso_days_ago(2)])  # alice's history

    # a fresh user (separate cookie jar) starts a streak of their own
    other = app.app.test_client()
    other.post("/register", json={"username": "b", "password": "x"})
    other.post("/login", json={"username": "b", "password": "x"})
    today = date.today().isoformat()
    assert other.get("/activity").get_json() == {
        "today": today,
        "streak": 1,
        "days": [today],
    }


# --- compute_streak (pure) -----------------------------------------------------


def test_compute_streak_empty():
    assert app.compute_streak(set(), date(2026, 7, 2)) == 0


def test_compute_streak_spans_month_boundary():
    days = {"2026-06-29", "2026-06-30", "2026-07-01"}
    assert app.compute_streak(days, date(2026, 7, 1)) == 3
