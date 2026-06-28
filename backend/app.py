import os
import sqlite3
from contextlib import closing
from functools import wraps

from flask import Flask, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

DATABASE = "users.db"
# The static study pages (homepage, content, solutions) live alongside the
# backend in ../frontend. Serving them from Flask keeps the pages and the API
# on the same origin, so the session cookie set at login is sent back on /me.
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
# Signs the session cookie used by auth. Override in production via the
# SECRET_KEY environment variable.
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")


def get_db():
    """Open a SQLite connection with rows accessible by column name."""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    """Create the tables if they don't exist yet (idempotent)."""
    with closing(get_db()) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )
        # Per-user study progress. The content pages are static, so they supply
        # the item identity (item_key) and a human label; the backend just stores
        # the checked/unchecked state per user. kind ("ref" | "problem") lets the
        # dashboard group items without needing a content data model.
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS progress (
                user_id    INTEGER NOT NULL REFERENCES users(id),
                item_key   TEXT    NOT NULL,
                kind       TEXT    NOT NULL,
                label      TEXT,
                done       INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT    NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (user_id, item_key)
            )
            """
        )
        db.commit()


def login_required(view):
    """Reject unauthenticated requests with 401; otherwise run the view."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_id") is None:
            return jsonify(error="authentication required"), 401
        return view(*args, **kwargs)

    return wrapped


# --- Pages -----------------------------------------------------------------


@app.get("/")
def index():
    """Serve the homepage; other static pages are served by static_folder."""
    return app.send_static_file("index.html")


# --- API -------------------------------------------------------------------


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify(error="username and password are required"), 400

    with closing(get_db()) as db:
        taken = db.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone()
        if taken is not None:
            return jsonify(error="username already taken"), 409

        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        db.commit()

    return jsonify(username=username), 201


@app.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify(error="username and password are required"), 400

    with closing(get_db()) as db:
        user = db.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify(error="invalid username or password"), 401

    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return jsonify(username=user["username"])


@app.post("/logout")
def logout():
    session.clear()
    return jsonify(status="logged out")


@app.get("/me")
@login_required
def me():
    return jsonify(id=session["user_id"], username=session["username"])


@app.get("/progress")
@login_required
def get_progress():
    """Return the current user's progress as a map keyed by item_key."""
    with closing(get_db()) as db:
        rows = db.execute(
            "SELECT item_key, kind, label, done FROM progress WHERE user_id = ?",
            (session["user_id"],),
        ).fetchall()
    return jsonify(
        {
            row["item_key"]: {
                "done": bool(row["done"]),
                "kind": row["kind"],
                "label": row["label"],
            }
            for row in rows
        }
    )


@app.post("/progress")
@login_required
def set_progress():
    """Upsert the done state for one item; the client sends the desired state."""
    data = request.get_json(silent=True) or {}
    item_key = (data.get("item_key") or "").strip()
    kind = (data.get("kind") or "").strip()
    label = (data.get("label") or "").strip()
    done = 1 if data.get("done") else 0
    if not item_key or not kind:
        return jsonify(error="item_key and kind are required"), 400

    with closing(get_db()) as db:
        db.execute(
            """
            INSERT INTO progress (user_id, item_key, kind, label, done, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(user_id, item_key) DO UPDATE SET
                done       = excluded.done,
                label      = excluded.label,
                kind       = excluded.kind,
                updated_at = excluded.updated_at
            """,
            (session["user_id"], item_key, kind, label, done),
        )
        db.commit()

    return jsonify(item_key=item_key, done=bool(done))


# Ensure the schema exists for both `python app.py` and `flask run`.
init_db()


if __name__ == "__main__":
    app.run(debug=True)
