# Projeto Maratona — Plan (easiest path: minimal auth)

## Goal
A **minimal but actually working** authentication system for Projeto Maratona:
register, login, logout, and one protected route — with the fewest moving parts.
This is the foundation; richer features (content, problem lists, progress) come later.

## Stack — Python + Flask + SQLite (session-cookie auth)
Chosen because it has essentially **one external dependency (Flask)**:
- Password hashing → `werkzeug.security` (ships with Flask)
- Sessions → Flask signed cookies
- Storage → `sqlite3` (Python standard library)
- Runs with a single `python app.py`.

## API (small JSON API — no HTML templates, to stay minimal)
- `POST /register` — `{username, password}` → create user (hashed password); `409` on
  duplicate, `400` on missing fields
- `POST /login` — `{username, password}` → set session cookie; `401` on bad credentials
- `POST /logout` — clear the session
- `GET /me` — **protected**; returns the logged-in user, or `401`
- `GET /health` — liveness check (added in scaffold)

## Files
```
projeto-maratona/
├── backend/
│   ├── app.py             # Flask app: routes, init_db(), auth logic, login_required
│   └── requirements.txt   # flask
├── frontend/              # static study pages (HTML + CSS)
├── .gitignore             # users.db, __pycache__/, venv/
└── README.md              # setup + run + endpoint usage
```

### `app.py` design
- `init_db()` runs at startup, creating `users(id INTEGER PRIMARY KEY, username TEXT UNIQUE
  NOT NULL, password_hash TEXT NOT NULL)` in `users.db` via `sqlite3`, using `IF NOT EXISTS`
  (idempotent).
- `app.secret_key` from env var `SECRET_KEY`, with a dev fallback (signs session cookies).
- `generate_password_hash` / `check_password_hash` from `werkzeug.security`.
- `login_required` decorator → `401` when `session.get('user_id')` is absent; applied to `/me`.
- All responses JSON; missing fields → `400`.

## Delivery — atomic PRs off `main`
No direct commits to `main`; each change is its own branch + one commit + a PR.
> Access note: the active `erickimai` token is read-only — run `gh auth switch` to the
> write account before any `git push` / `gh pr create`.

1. `chore/scaffold` — `requirements.txt`, `.gitignore`, `app.py` (Flask app, `secret_key`
   from env, `init_db()` + `users` table, `GET /health`). Runs, no auth yet.
2. `feat/register` — `POST /register` with hashing + duplicate/validation handling.
3. `feat/login-logout` — `POST /login` (verify, set `session['user_id']`) + `POST /logout`.
4. `feat/protected-me` — `login_required` decorator + protected `GET /me`.
5. `docs/readme` — update `README.md` (setup, run, endpoint usage).

## Verification (end to end)
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py                      # http://127.0.0.1:5000

# register, then duplicate -> 409
curl -s -X POST localhost:5000/register -H 'Content-Type: application/json' -d '{"username":"alice","password":"secret"}'
curl -s -X POST localhost:5000/register -H 'Content-Type: application/json' -d '{"username":"alice","password":"secret"}'
# protected without login -> 401
curl -s -i localhost:5000/me
# login (save cookie) -> then /me with cookie -> 200
curl -s -c jar.txt -X POST localhost:5000/login -H 'Content-Type: application/json' -d '{"username":"alice","password":"secret"}'
curl -s -b jar.txt localhost:5000/me
# wrong password -> 401 ; logout then /me -> 401
curl -s -i -X POST localhost:5000/login -H 'Content-Type: application/json' -d '{"username":"alice","password":"wrong"}'
curl -s -b jar.txt -X POST localhost:5000/logout && curl -s -i -b jar.txt localhost:5000/me
```
Confirm `users.db` is created and gitignored.

## Out of scope / follow-ups
Learning-grade: no CSRF tokens, no rate limiting, no email verification — fine for a course
demo, flag before any production use. Easy extensions later: HTML login form + templates, a
JWT variant for an SPA frontend, or swapping SQLite → PostgreSQL. The fuller Next.js learning
platform remains an option (see archived plan `linear-nibbling-hartmanis.md`).
