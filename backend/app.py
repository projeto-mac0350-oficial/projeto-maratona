import os
import sqlite3
from contextlib import closing
from datetime import date, timedelta
from functools import wraps

from flask import Flask, jsonify, request, session, render_template, redirect
from werkzeug.security import check_password_hash, generate_password_hash

DATABASE = "users.db"
# The static study pages (homepage, content, solutions) live alongside the
# backend in ../frontend. Serving them from Flask keeps the pages and the API
# on the same origin, so the session cookie set at login is sent back on /me.
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

app = Flask(__name__, template_folder=FRONTEND_DIR, static_folder=FRONTEND_DIR, static_url_path="")
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
                password_hash TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        cols = {
            row["name"]
            for row in db.execute("PRAGMA table_info(users)")
        }

        if "is_admin" not in cols:
            db.execute("""
                ALTER TABLE users
                ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0
            """)
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
        # User-defined study goals ("Suas metas"). No "done" flag: checking a
        # goal off is treated as completing it, so the row is deleted rather
        # than kept around — matches the UI, where the goal just disappears.
        # due_day/due_month are optional and have no year (a recurring
        # day/month reminder, e.g. "15/08"), so they're plain small ints.
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS goals (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                description TEXT    NOT NULL,
                due_day     INTEGER,
                due_month   INTEGER,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        # One row per (user, calendar day) the user was seen authenticated —
        # recorded on login and on /me, so staying logged in via the session
        # cookie still counts. Day is the server-local date ('YYYY-MM-DD');
        # powers the homepage mini calendar and the streak.
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS login_days (
                user_id INTEGER NOT NULL REFERENCES users(id),
                day     TEXT    NOT NULL,
                PRIMARY KEY (user_id, day)
            )
            """
        )
        # Levels group topics into separate lists/pages (e.g. Nível 1, 2, 3).
        # Seeded from SEED_LEVELS below, same idempotent-upsert pattern as topics.
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS levels (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                slug     TEXT UNIQUE NOT NULL,
                title    TEXT NOT NULL,
                position INTEGER NOT NULL DEFAULT 0
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
                level_id INTEGER REFERENCES levels(id),
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
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS problem_solutions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id     INTEGER NOT NULL REFERENCES topic_items(id),
                statement   TEXT,
                explanation TEXT,
                code        TEXT,
                UNIQUE(item_id)
            )
            """
        )
        # Lightweight migration: add columns introduced after a DB was first
        # created (CREATE TABLE IF NOT EXISTS won't alter an existing table).
        existing = {row["name"] for row in db.execute("PRAGMA table_info(topic_items)")}
        if "difficulty" not in existing:
            db.execute("ALTER TABLE topic_items ADD COLUMN difficulty TEXT")
        existing_topics = {row["name"] for row in db.execute("PRAGMA table_info(topics)")}
        if "level_id" not in existing_topics:
            db.execute("ALTER TABLE topics ADD COLUMN level_id INTEGER REFERENCES levels(id)")
        db.commit()
    seed_levels()
    seed_content()


# The lists shown under the "Níveis" menu, each with its own topics page
# (/conteudos?level=<slug>). Position controls both the menu order and the
# order topics are grouped in.
SEED_LEVELS = [
    {"slug": "nivel_1", "title": "Nível 1"},
    {"slug": "nivel_2", "title": "Nível 2"},
    {"slug": "nivel_3", "title": "Nível 3"},
]


def seed_levels():
    """Upsert SEED_LEVELS into the levels table (idempotent, by slug)."""
    with closing(get_db()) as db:
        for pos, level in enumerate(SEED_LEVELS):
            db.execute(
                """
                INSERT INTO levels (slug, title, position)
                VALUES (?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    title    = excluded.title,
                    position = excluded.position
                """,
                (level["slug"], level["title"], pos),
            )
        db.commit()


# Course-authored study content. Each topic lists references to read and
# problems to solve; "url" is the external link, "solution_url" the local
# solution page. "level" must match a slug in SEED_LEVELS — it's what groups
# the topic under a given /conteudos?level=<slug> page. To add material, edit
# this structure — the schema and API stay the same. Item order here is the
# order shown to the student.
SEED_CONTENT = [
    {
        "slug": "busca_binaria",
        "level": "nivel_1",
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
                "solution": {
                    "statement": """
                   In an under-construction village, n houses have been built in a row numbered from 1 to n. House i has hospitality hi.

The village has n−1 roads, where road i connects houses i and i+1 and will be built on day di. Initially, no roads are built.

You start at house x and will stay in the village from day 1 to day k, initially with a satisfaction of 0. On day s, the following happens in order:

 -   All roads i with di=s are built;
  -  You may move to an adjacent house, if the road to it has been built, or stay at your current house;
   - Your satisfaction increases by hj, where j is the house you are currently at. 

Find the maximum satisfaction you can achieve after k days.
                    """,

                    "explanation": """
                    A ideia é usar busca binária porque...
                    """,

                    "code": """#include <bits/stdc++.h>
using namespace std;

int main() {
    return 0;
}
                    """
                }
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
            level_row = db.execute(
                "SELECT id FROM levels WHERE slug = ?", (topic["level"],)
            ).fetchone()
            level_id = level_row["id"] if level_row else None
            db.execute(
                """
                INSERT INTO topics (slug, title, summary, level_id, position)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    title    = excluded.title,
                    summary  = excluded.summary,
                    level_id = excluded.level_id,
                    position = excluded.position
                """,
                (topic["slug"], topic["title"], topic["summary"], level_id, t_pos),
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
                    
                    # Pega o id do topic_item criado
                    item_id = db.execute(
                        """
                        SELECT id
                        FROM topic_items
                        WHERE topic_id = ?
                        AND kind = ?
                        AND slug = ?
                        """,
                        (
                            topic_id,
                            kind,
                            item["slug"],
                        ),
                    ).fetchone()["id"]


                    # Se for problema, cria a solução associada
                    if kind == "problem" and "solution" in item:
                        db.execute(
                            """
                            INSERT INTO problem_solutions
                                (
                                    item_id,
                                    statement,
                                    explanation,
                                    code
                                )
                            VALUES (?, ?, ?, ?)

                            ON CONFLICT(item_id) DO UPDATE SET
                                statement   = excluded.statement,
                                explanation = excluded.explanation,
                                code        = excluded.code
                            """,
                            (
                                item_id,
                                item["solution"]["statement"],
                                item["solution"]["explanation"],
                                item["solution"]["code"],
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

def admin_required(view):
    """Permite acesso apenas para administradores."""

    @wraps(view)
    def wrapped(*args, **kwargs):

        if session.get("user_id") is None:
            return jsonify(error="authentication required"), 401

        with closing(get_db()) as db:
            user = db.execute(
                """
                SELECT is_admin
                FROM users
                WHERE id = ?
                """,
                (session["user_id"],),
            ).fetchone()

        if user is None or user["is_admin"] == 0:
            return jsonify(error="admin only"), 403

        return view(*args, **kwargs)

    return wrapped

def record_login_day(user_id):
    """Mark today (server-local) as a day this user was active (idempotent)."""
    with closing(get_db()) as db:
        db.execute(
            "INSERT OR IGNORE INTO login_days (user_id, day) VALUES (?, ?)",
            (user_id, date.today().isoformat()),
        )
        db.commit()


def compute_streak(days, today):
    """Count consecutive days ending at `today` present in `days` (ISO strings)."""
    streak = 0
    d = today
    while d.isoformat() in days:
        streak += 1
        d -= timedelta(days=1)
    return streak


# --- Pages -----------------------------------------------------------------


@app.get("/")
def index():
    """Serve the homepage; other static pages are served by static_folder."""
    return render_template("index.html")


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
            """
            SELECT id, username, password_hash, is_admin
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify(error="invalid username or password"), 401

    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]

    record_login_day(user["id"])

    return jsonify(
        id=user["id"],
        username=user["username"],
        is_admin=bool(user["is_admin"])
    )

@app.post("/logout")
def logout():
    session.clear()
    return jsonify(status="logged out")


@app.get("/me")
@login_required
def me():
    record_login_day(session["user_id"])

    with closing(get_db()) as db:
        user = db.execute(
            """
            SELECT is_admin
            FROM users
            WHERE id = ?
            """,
            (session["user_id"],),
        ).fetchone()

    return jsonify(
        id=session["user_id"],
        username=session["username"],
        is_admin=bool(user["is_admin"]),
    )


@app.get("/activity")
@login_required
def get_activity():
    """Record today's visit; return this month's logged-in days + streak."""
    user_id = session["user_id"]
    record_login_day(user_id)
    today = date.today()
    with closing(get_db()) as db:
        rows = db.execute(
            "SELECT day FROM login_days WHERE user_id = ?", (user_id,)
        ).fetchall()
    all_days = {row["day"] for row in rows}
    month_prefix = today.strftime("%Y-%m-")
    return jsonify(
        today=today.isoformat(),
        streak=compute_streak(all_days, today),
        days=sorted(d for d in all_days if d.startswith(month_prefix)),
    )


@app.get("/heatmap")
@login_required
def get_heatmap():
    """Per-day count of progress items marked done, keyed by date — powers the
    profile heatmap. Derived from progress.updated_at, so it reflects the last
    time each item's done state changed, not a full history of toggles."""
    with closing(get_db()) as db:
        rows = db.execute(
            """
            SELECT substr(updated_at, 1, 10) AS day, COUNT(*) AS count
            FROM progress
            WHERE user_id = ? AND done = 1
            GROUP BY day
            """,
            (session["user_id"],),
        ).fetchall()
    return jsonify(
        today=date.today().isoformat(),
        counts={row["day"]: row["count"] for row in rows},
    )


@app.get("/progress")
@login_required
def get_progress():
    """Return the current user's progress as a map keyed by item_key."""
    with closing(get_db()) as db:
        rows = db.execute(
            "SELECT item_key, kind, label, done, updated_at FROM progress WHERE user_id = ?",
            (session["user_id"],),
        ).fetchall()
    return jsonify(
        {
            row["item_key"]: {
                "done": bool(row["done"]),
                "kind": row["kind"],
                "label": row["label"],
                "updated_at": row["updated_at"],
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


# --- Goals ("Suas metas") ---------------------------------------------------
#
# Simple per-user to-do list shown on the profile page. There's no "done"
# flag: checking a goal off completes it, and the UI just makes it disappear —
# so the backend mirrors that by deleting the row instead of tracking state.
 
MAX_GOAL_DESCRIPTION_LENGTH = 100
 
 
@app.get("/goals")
@login_required
def list_goals():
    """List the current user's goals, oldest first."""
    with closing(get_db()) as db:
        rows = db.execute(
            """
            SELECT id, description, due_day, due_month FROM goals
            WHERE user_id = ? ORDER BY id
            """,
            (session["user_id"],),
        ).fetchall()
    return jsonify([dict(row) for row in rows])
 
 
@app.post("/goals")
@login_required
def create_goal():
    """Create a goal. due_day/due_month are optional but must come together."""
    data = request.get_json(silent=True) or {}
    description = (data.get("description") or "").strip()
    if not description:
        return jsonify(error="description is required"), 400
    if len(description) > MAX_GOAL_DESCRIPTION_LENGTH:
        return jsonify(
            error=f"description must be at most {MAX_GOAL_DESCRIPTION_LENGTH} characters"
        ), 400
 
    due_day = data.get("due_day")
    due_month = data.get("due_month")
    if (due_day is None) != (due_month is None):
        return jsonify(error="due_day and due_month must be given together"), 400
    if due_day is not None:
        try:
            due_day = int(due_day)
            due_month = int(due_month)
        except (TypeError, ValueError):
            return jsonify(error="due_day and due_month must be integers"), 400
        if not (1 <= due_day <= 31) or not (1 <= due_month <= 12):
            return jsonify(error="invalid due date"), 400
 
    with closing(get_db()) as db:
        cur = db.execute(
            """
            INSERT INTO goals (user_id, description, due_day, due_month)
            VALUES (?, ?, ?, ?)
            """,
            (session["user_id"], description, due_day, due_month),
        )
        db.commit()
        goal_id = cur.lastrowid
 
    return jsonify(
        id=goal_id, description=description, due_day=due_day, due_month=due_month
    ), 201
 
 
@app.delete("/goals/<int:goal_id>")
@login_required
def delete_goal(goal_id):
    """Delete one of the current user's goals (completing it, in UI terms)."""
    with closing(get_db()) as db:
        db.execute(
            "DELETE FROM goals WHERE id = ? AND user_id = ?",
            (goal_id, session["user_id"]),
        )
        db.commit()
    return jsonify(deleted=True)
 

# --- Levels ------------------------------------------------------------


@app.get("/levels")
def list_levels():
    """List the levels (e.g. Nível 1, 2, 3) that power the "Níveis" menu."""
    with closing(get_db()) as db:
        rows = db.execute(
            "SELECT slug, title FROM levels ORDER BY position, id"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/levels/<slug>")
def get_level(slug):
    """Return one level with its topics (summary only, no items) — this is
    what /conteudos?level=<slug> fetches to render its list of cards."""
    with closing(get_db()) as db:
        level = db.execute(
            "SELECT id, slug, title FROM levels WHERE slug = ?", (slug,)
        ).fetchone()
        if level is None:
            return jsonify(error="level not found"), 404
        topics = db.execute(
            """
            SELECT slug, title, summary FROM topics
            WHERE level_id = ? ORDER BY position, id
            """,
            (level["id"],),
        ).fetchall()
    return jsonify(
        slug=level["slug"],
        title=level["title"],
        topics=[dict(row) for row in topics],
    )


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
            """
            SELECT t.id, t.slug, t.title, t.summary, l.slug AS level
            FROM topics t
            LEFT JOIN levels l
            ON t.level_id = l.id
            WHERE t.slug = ?""", 
            (slug,)
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
        level=topic["level"],
        references=[_serialize_item(slug, r) for r in items if r["kind"] == "ref"],
        problems=[_serialize_item(slug, r) for r in items if r["kind"] == "problem"],
    )


@app.get("/conteudo")
def conteudo():
    """Serve the generic topic page (must go through Jinja, not static, since
    it extends base.html). The slug itself is read client-side from
    ?topic=<slug> by the page's own script."""
    return render_template("topic.html")

@app.get("/conteudos")
def conteudos():
    """Serve the topics list page (cards linking to /conteudo?topic=<slug>)."""
    return render_template("topics-list.html")


# ---- Perfil ------------------------------------------------------------

@app.get("/perfil")
@login_required
def perfil():

    with closing(get_db()) as db:
        admin = db.execute(
            """
            SELECT is_admin
            FROM users
            WHERE id = ?
            """,
            (session["user_id"],),
        ).fetchone()

    return render_template(
        "profile.html",
        is_admin=bool(admin["is_admin"])
    )

@app.get("/admin")
@login_required
@admin_required
def admin():
    return render_template("pagina_admin.html")

def _slugify(text):
    """Same convention used elsewhere in this file for problem/reference
    slugs: lowercase, spaces -> hyphens. Good enough for the short titles
    coming out of the admin forms."""
    return text.strip().lower().replace(" ", "-")


def _unique_topic_slug(db, base_slug):
    """Append -2, -3, ... to base_slug until it doesn't collide with an
    existing topic (topics.slug is UNIQUE)."""
    slug = base_slug
    suffix = 2
    while db.execute(
        "SELECT 1 FROM topics WHERE slug = ?", (slug,)
    ).fetchone() is not None:
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    return slug


@app.get("/admin/topics/new")
@login_required
@admin_required
def admin_new():
    with closing(get_db()) as db:
        levels = db.execute(
            """
            SELECT slug, title
            FROM levels
            ORDER BY position
            """
        ).fetchall()

    return render_template(
        "pagina_admin_novo.html",
        levels=levels,
    )


@app.post("/admin/topics/new")
@login_required
@admin_required
def admin_create():

    title = (request.form.get("title") or "").strip()
    summary = request.form.get("summary")
    level = request.form.get("level")

    if not title:
        return "O título é obrigatório", 400

    with closing(get_db()) as db:

        level_row = db.execute(
            "SELECT id FROM levels WHERE slug = ?", (level,)
        ).fetchone()
        level_id = level_row["id"] if level_row else None

        slug = _unique_topic_slug(db, _slugify(title))

        # Cria o tópico
        next_position = db.execute(
            "SELECT COALESCE(MAX(position) + 1, 0) FROM topics"
        ).fetchone()[0]

        cursor = db.execute(
            """
            INSERT INTO topics (slug, title, summary, level_id, position)
            VALUES (?, ?, ?, ?, ?)
            """,
            (slug, title, summary, level_id, next_position),
        )
        topic_id = cursor.lastrowid

        # Referências
        new_ref_titles = request.form.getlist("new_ref_title")
        new_ref_urls = request.form.getlist("new_ref_url")

        for i in range(len(new_ref_titles)):

            if not new_ref_titles[i].strip():
                continue

            ref_slug = _slugify(new_ref_titles[i])

            db.execute(
                """
                INSERT INTO topic_items
                (topic_id, kind, slug, title, url, position)
                VALUES (?, 'ref', ?, ?, ?, ?)
                """,
                (topic_id, ref_slug, new_ref_titles[i], new_ref_urls[i], i),
            )

        # Problemas
        new_titles = request.form.getlist("new_problem_title")
        new_urls = request.form.getlist("new_problem_url")
        new_difficulties = request.form.getlist("new_problem_difficulty")
        new_statements = request.form.getlist("new_problem_statement")
        new_explanations = request.form.getlist("new_problem_explanation")
        new_codes = request.form.getlist("new_problem_code")

        for i in range(len(new_titles)):

            if not new_titles[i].strip():
                continue

            problem_slug = _slugify(new_titles[i])

            cursor = db.execute(
                """
                INSERT INTO topic_items
                (topic_id, kind, slug, title, url, solution_url, difficulty, position)
                VALUES (?, 'problem', ?, ?, ?, ?, ?, ?)
                """,
                (
                    topic_id,
                    problem_slug,
                    new_titles[i],
                    new_urls[i],
                    "solucao.html",
                    new_difficulties[i],
                    i,
                ),
            )

            item_id = cursor.lastrowid

            db.execute(
                """
                INSERT INTO problem_solutions
                (item_id, statement, explanation, code)
                VALUES (?, ?, ?, ?)
                """,
                (
                    item_id,
                    new_statements[i],
                    new_explanations[i],
                    new_codes[i],
                ),
            )

        db.commit()

    return redirect("/admin")


@app.get("/admin/topics/<slug>/edit")
@login_required
@admin_required
def admin_edit(slug):

    with closing(get_db()) as db:

        topic = db.execute(
            """
            SELECT 
                t.id,
                t.slug,
                t.title,
                t.summary,
                l.slug AS level
            FROM topics t
            LEFT JOIN levels l
                ON l.id = t.level_id
            WHERE t.slug = ?
            """,
            (slug,)
        ).fetchone()


        if topic is None:
            return "Conteúdo não encontrado", 404


        references = db.execute(
            """
            SELECT *
            FROM topic_items
            WHERE topic_id = ?
            AND kind = 'ref'
            ORDER BY position
            """,
            (topic["id"],)
        ).fetchall()


        problems = db.execute(
            """
            SELECT
                ti.id,
                ti.slug,
                ti.title,
                ti.url,
                ti.difficulty,
                ps.statement,
                ps.explanation,
                ps.code
            FROM topic_items ti
            LEFT JOIN problem_solutions ps
                ON ps.item_id = ti.id
            WHERE ti.topic_id = ?
            AND ti.kind = 'problem'
            ORDER BY ti.position
            """,
            (topic["id"],)
        ).fetchall()


        levels = db.execute(
            """
            SELECT slug, title
            FROM levels
            ORDER BY position
            """
        ).fetchall()


    return render_template(
        "pagina_admin_editar.html",
        topic=topic,
        references=references,
        problems=problems,
        levels=levels
    )

@app.post("/admin/topics/<slug>/edit")
@login_required
@admin_required
def admin_update(slug):

    title = request.form["title"]
    summary = request.form["summary"]
    level = request.form["level"]

    with closing(get_db()) as db:
        topic_row = db.execute(
            """
            SELECT id
            FROM topics
            WHERE slug = ?
            """,
            (slug,)
        ).fetchone()

        topic_id = topic_row["id"]

        level_id = db.execute(
            """
            SELECT id FROM levels
            WHERE slug = ?
            """,
            (level,)
        ).fetchone()["id"]


        # Atualiza tópico
        db.execute(
            """
            UPDATE topics
            SET title = ?,
                summary = ?,
                level_id = ?
            WHERE slug = ?
            """,
            (
                title,
                summary,
                level_id,
                slug
            )
        )


        # Atualiza problemas
        problem_ids = request.form.getlist("problem_id")
        titles = request.form.getlist("problem_title")
        urls = request.form.getlist("problem_url")
        difficulties = request.form.getlist("problem_difficulty")
        statements = request.form.getlist("problem_statement")
        explanations = request.form.getlist("problem_explanation")
        codes = request.form.getlist("problem_code")


        for i, problem_id in enumerate(problem_ids):

            db.execute(
                """
                UPDATE topic_items
                SET title = ?,
                    url = ?,
                    difficulty = ?
                WHERE id = ?
                """,
                (
                    titles[i],
                    urls[i],
                    difficulties[i],
                    problem_id
                )
            )


            db.execute(
                """
                UPDATE problem_solutions
                SET statement = ?,
                    explanation = ?,
                    code = ?
                WHERE item_id = ?
                """,
                (
                    statements[i],
                    explanations[i],
                    codes[i],
                    problem_id
                )
            )

        new_titles = request.form.getlist("new_problem_title")
        new_urls = request.form.getlist("new_problem_url")
        new_difficulties = request.form.getlist("new_problem_difficulty")
        new_statements = request.form.getlist("new_problem_statement")
        new_explanations = request.form.getlist("new_problem_explanation")
        new_codes = request.form.getlist("new_problem_code")


        for i in range(len(new_titles)):

            # ignora campos vazios
            if not new_titles[i].strip():
                continue


            problem_slug = new_titles[i].lower().replace(" ", "-")


            # pega a próxima posição disponível
            next_position = db.execute(
                """
                SELECT COALESCE(MAX(position) + 1, 0)
                FROM topic_items
                WHERE topic_id = ?
                AND kind = 'problem'
                """,
                (topic_id,)
            ).fetchone()[0]


            cursor = db.execute(
                """
                INSERT INTO topic_items
                (
                    topic_id,
                    kind,
                    slug,
                    title,
                    url,
                    solution_url,
                    difficulty,
                    position
                )
                VALUES (?, 'problem', ?, ?, ?, ?, ?, ?)
                """,
                (
                    topic_id,
                    problem_slug,
                    new_titles[i],
                    new_urls[i],
                    "solucao.html",
                    new_difficulties[i],
                    next_position
                )
            )


            item_id = cursor.lastrowid


            db.execute(
                """
                INSERT INTO problem_solutions
                (
                    item_id,
                    statement,
                    explanation,
                    code
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    item_id,
                    new_statements[i],
                    new_explanations[i],
                    new_codes[i]
                )
            )

        new_ref_titles = request.form.getlist("new_ref_title")
        new_ref_urls = request.form.getlist("new_ref_url")


        for i in range(len(new_ref_titles)):

            if not new_ref_titles[i].strip():
                continue


            ref_slug = (
                new_ref_titles[i]
                .lower()
                .replace(" ", "-")
            )


            next_position = db.execute(
                """
                SELECT COALESCE(MAX(position)+1,0)
                FROM topic_items
                WHERE topic_id = ?
                AND kind = 'ref'
                """,
                (topic_id,)
            ).fetchone()[0]


            db.execute(
                """
                INSERT INTO topic_items
                (
                    topic_id,
                    kind,
                    slug,
                    title,
                    url,
                    position
                )
                VALUES (?, 'ref', ?, ?, ?, ?)
                """,
                (
                    topic_id,
                    ref_slug,
                    new_ref_titles[i],
                    new_ref_urls[i],
                    next_position
                )
            )

        db.commit()


    return redirect("/admin")

@app.get("/admin/topics")
@login_required
@admin_required
def admin_topics():

    with closing(get_db()) as db:

        rows = db.execute(
            """
            SELECT
                t.slug,
                t.title,
                l.title AS level
            FROM topics t
            JOIN levels l
                ON l.id = t.level_id
            ORDER BY l.position, t.position
            """
        ).fetchall()

    return jsonify([dict(r) for r in rows])

@app.delete("/admin/topics/<slug>")
@login_required
@admin_required
def delete_topic(slug):
    """Apaga o tópico e tudo que depende dele (itens e soluções)."""

    with closing(get_db()) as db:

        topic = db.execute(
            "SELECT id FROM topics WHERE slug = ?", (slug,)
        ).fetchone()

        if topic is None:
            return jsonify(error="topic not found"), 404

        topic_id = topic["id"]

        item_ids = [
            row["id"]
            for row in db.execute(
                "SELECT id FROM topic_items WHERE topic_id = ?", (topic_id,)
            ).fetchall()
        ]

        for item_id in item_ids:
            db.execute(
                "DELETE FROM problem_solutions WHERE item_id = ?", (item_id,)
            )

        db.execute("DELETE FROM topic_items WHERE topic_id = ?", (topic_id,))
        db.execute("DELETE FROM topics WHERE id = ?", (topic_id,))

        db.commit()

    return jsonify(success=True)

@app.delete("/admin/problems/<int:problem_id>")
@login_required
@admin_required
def delete_problem(problem_id):

    with closing(get_db()) as db:

        db.execute(
            """
            DELETE FROM problem_solutions
            WHERE item_id = ?
            """,
            (problem_id,)
        )

        db.execute(
            """
            DELETE FROM topic_items
            WHERE id = ?
            """,
            (problem_id,)
        )

        db.commit()

    return jsonify(success=True)

@app.delete("/admin/references/<int:ref_id>")
@login_required
@admin_required
def delete_reference(ref_id):

    with closing(get_db()) as db:

        db.execute(
            """
            DELETE FROM topic_items
            WHERE id = ?
            AND kind = 'ref'
            """,
            (ref_id,)
        )

        db.commit()

    return jsonify(success=True)

# --- Solutions -------------------------------------

@app.get("/solucao")
def solucao():
    return render_template("solution.html")

@app.get("/solutions/<slug>")
def get_solution(slug):
    with closing(get_db()) as db:
        solution = db.execute(
            """
            SELECT 
                ti.title,
                ti.url,
                ps.statement,
                ps.explanation,
                ps.code,
                t.slug AS topic_slug
            FROM topic_items ti
            JOIN problem_solutions ps
                ON ps.item_id = ti.id
            JOIN topics t
                ON t.id = ti.topic_id
            WHERE ti.slug = ?
            """,
            (slug,)
        ).fetchone()

    if solution is None:
        return jsonify(error="solution not found"), 404

    return jsonify(
        title=solution["title"],
        url=solution["url"],
        statement=solution["statement"],
        explanation=solution["explanation"],
        code=solution["code"],
        topic_slug=solution["topic_slug"]
    )

# Ensure the schema exists for both `python app.py` and `flask run`.
init_db()


if __name__ == "__main__":
    app.run(debug=True)