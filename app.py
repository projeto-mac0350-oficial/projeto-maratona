import os
import sqlite3

from flask import Flask, jsonify

DATABASE = "users.db"

app = Flask(__name__)
# Signs the session cookie used by auth (added in a later PR). Override in
# production via the SECRET_KEY environment variable.
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")


def init_db():
    """Create the users table if it doesn't exist yet (idempotent)."""
    db = sqlite3.connect(DATABASE)
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
    db.close()


@app.get("/health")
def health():
    return jsonify(status="ok")


# Ensure the schema exists for both `python app.py` and `flask run`.
init_db()


if __name__ == "__main__":
    app.run(debug=True)
