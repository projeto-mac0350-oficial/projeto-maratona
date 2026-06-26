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
    """Create the users table if it doesn't exist yet (idempotent)."""
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


# Ensure the schema exists for both `python app.py` and `flask run`.
init_db()


if __name__ == "__main__":
    app.run(debug=True)
