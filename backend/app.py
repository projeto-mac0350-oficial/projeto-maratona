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
        # Study content: topics and their items (references to read + problems to
        # solve). This is course-authored reference data — read-only over the API
        # and seeded from SEED_CONTENT below, so adding a topic means editing data,
        # not hand-writing an HTML page.
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS topics (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                slug     TEXT UNIQUE NOT NULL,
                title    TEXT NOT NULL,
                summary  TEXT,
                position INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS topic_items (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id     INTEGER NOT NULL REFERENCES topics(id),
                kind         TEXT    NOT NULL,   -- 'ref' | 'problem'
                slug         TEXT    NOT NULL,
                title        TEXT    NOT NULL,
                url          TEXT,               -- reference / problem-statement link
                solution_url TEXT,               -- problems only
                difficulty   TEXT,               -- problems only: 'easy' | 'medium' | 'hard'
                position     INTEGER NOT NULL DEFAULT 0,
                UNIQUE (topic_id, kind, slug)
            )
            """
        )
        # Lightweight migration: add columns introduced after a DB was first
        # created (CREATE TABLE IF NOT EXISTS won't alter an existing table).
        existing = {row["name"] for row in db.execute("PRAGMA table_info(topic_items)")}
        if "difficulty" not in existing:
            db.execute("ALTER TABLE topic_items ADD COLUMN difficulty TEXT")
        db.commit()
    seed_content()


# Course-authored study content. Each topic lists references to read and
# problems to solve; "url" is the external link, "solution_url" the local
# solution page. To add material, edit this structure — the schema and API
# stay the same. Item order here is the order shown to the student.
SEED_CONTENT = [
    {
        "slug": "busca_binaria",
        "title": "Busca Binária",
        "summary": (
            "A busca binária é um algoritmo eficiente de divisão e conquista "
            "usado para encontrar um valor específico em uma lista ordenada. "
            "Ela reduz drasticamente o tempo de pesquisa ao dividir o espaço de "
            "busca pela metade a cada comparação, descartando a parte onde o "
            "elemento não pode estar."
        ),
        "references": [
            {
                "slug": "cp-algorithms",
                "title": "CP-Algorithms",
                "url": "https://cp-algorithms.com/num_methods/binary_search.html",
            },
            {
                "slug": "noic",
                "title": "NOIC - Busca Binária",
                "url": "https://noic.com.br/materiais-informatica/curso/techniques-01/",
            },
            {"slug": "exemplos-praticos", "title": "Exemplos práticos", "url": None},
        ],
        "problems": [
            {
                "slug": "roadworks",
                "title": "Roadworks",
                "url": "https://codeforces.com/problemset/problem/2229/G?mobile=true",
                "solution_url": "solucao.html",
                "difficulty": "easy",
            },
            {
                "slug": "nome-2",
                "title": "Nome 2",
                "url": None,
                "solution_url": "solucao.html",
                "difficulty": "medium",
            },
            {
                "slug": "nome-3",
                "title": "Nome 3",
                "url": "https://codeforces.com/problemset/problem/1/C",
                "solution_url": "solucao.html",
                "difficulty": "hard",
            },
        ],
    },
]


def seed_content():
    """Upsert SEED_CONTENT into the topics tables (idempotent, by slug)."""
    with closing(get_db()) as db:
        for t_pos, topic in enumerate(SEED_CONTENT):
            db.execute(
                """
                INSERT INTO topics (slug, title, summary, position)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    title    = excluded.title,
                    summary  = excluded.summary,
                    position = excluded.position
                """,
                (topic["slug"], topic["title"], topic["summary"], t_pos),
            )
            topic_id = db.execute(
                "SELECT id FROM topics WHERE slug = ?", (topic["slug"],)
            ).fetchone()["id"]
            for kind, key in (("ref", "references"), ("problem", "problems")):
                for i_pos, item in enumerate(topic.get(key, [])):
                    db.execute(
                        """
                        INSERT INTO topic_items
                            (topic_id, kind, slug, title, url, solution_url, difficulty, position)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(topic_id, kind, slug) DO UPDATE SET
                            title        = excluded.title,
                            url          = excluded.url,
                            solution_url = excluded.solution_url,
                            difficulty   = excluded.difficulty,
                            position     = excluded.position
                        """,
                        (
                            topic_id,
                            kind,
                            item["slug"],
                            item["title"],
                            item.get("url"),
                            item.get("solution_url"),
                            item.get("difficulty"),
                            i_pos,
                        ),
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


# --- Content ---------------------------------------------------------------


def _serialize_item(topic_slug, row):
    """Shape a topic_items row for the API, deriving the progress item_key and
    the dashboard label so the frontend doesn't have to know the conventions."""
    short = "prob" if row["kind"] == "problem" else "ref"
    item = {
        "slug": row["slug"],
        "title": row["title"],
        "kind": row["kind"],
        "url": row["url"],
        "item_key": f"{topic_slug}:{short}:{row['slug']}",
        # Problems show a 1-based number on the dashboard; refs use their title.
        "label": (
            f"Problema {row['position'] + 1} - {row['title']}"
            if row["kind"] == "problem"
            else row["title"]
        ),
    }
    if row["kind"] == "problem":
        item["solution_url"] = row["solution_url"]
        item["difficulty"] = row["difficulty"]
    return item


@app.get("/topics")
def list_topics():
    """List the available study topics (summary only — no items)."""
    with closing(get_db()) as db:
        rows = db.execute(
            "SELECT slug, title, summary FROM topics ORDER BY position, id"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/topics/<slug>")
def get_topic(slug):
    """Return one topic with its references and problems, in authoring order."""
    with closing(get_db()) as db:
        topic = db.execute(
            "SELECT id, slug, title, summary FROM topics WHERE slug = ?", (slug,)
        ).fetchone()
        if topic is None:
            return jsonify(error="topic not found"), 404
        items = db.execute(
            """
            SELECT kind, slug, title, url, solution_url, difficulty, position
            FROM topic_items WHERE topic_id = ? ORDER BY position, id
            """,
            (topic["id"],),
        ).fetchall()

    return jsonify(
        slug=topic["slug"],
        title=topic["title"],
        summary=topic["summary"],
        references=[_serialize_item(slug, r) for r in items if r["kind"] == "ref"],
        problems=[_serialize_item(slug, r) for r in items if r["kind"] == "problem"],
    )


# Ensure the schema exists for both `python app.py` and `flask run`.
init_db()


if __name__ == "__main__":
    app.run(debug=True)
