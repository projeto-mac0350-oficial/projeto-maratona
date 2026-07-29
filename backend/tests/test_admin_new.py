import app as flask_app

# --------- GET /admin/topics/new ------------------------

def test_admin_can_open_new_topic_page(admin_client):
    response = admin_client.get("/admin/topics/new")
    assert response.status_code == 200

def test_normal_user_cannot_open_new_topic_page(auth_client):
    response = auth_client.get("/admin/topics/new")
    assert response.status_code == 403

# --------- POST /admin/topics/new ----------------------------

def test_admin_creates_topic_in_database(admin_client):
    admin_client.post( "/admin/topics/new",
        data={
            "title": "BFS",
            "summary": "Busca em Largura",
            "level": "nivel_1"
        }
    )

    with flask_app.get_db() as db:
        topic = db.execute(
            "SELECT * FROM topics WHERE title = ?",
            ("BFS",)
        ).fetchone()

    assert topic is not None
    assert topic["summary"] == "Busca em Largura"

def test_normal_user_cannot_create_topic(auth_client):
    response = auth_client.post(
        "/admin/topics/new",
        data={
            "title": "Tentativa",
            "summary": "Resumo",
            "level": "nivel_1"
        }
    )

    assert response.status_code == 403

def test_anonymous_cannot_create_topic(client):
    response = client.post(
        "/admin/topics/new",
        data={
            "title": "Tentativa",
            "summary": "Resumo",
            "level": "nivel_1"
        }
    )

    assert response.status_code == 401

def test_admin_creates_reference(admin_client):

    admin_client.post(
        "/admin/topics/new",
        data={
            "title": "BFS",
            "summary": "Resumo",
            "level": "nivel_1",

            "new_ref_title": [
                "CP Algorithms"
            ],

            "new_ref_url": [
                "https://cp-algorithms.com/graph/breadth-first-search.html"
            ]
        }
    )

    with flask_app.get_db() as db:
        ref = db.execute(
            """
            SELECT *
            FROM topic_items
            WHERE title = ?
            """,
            ("CP Algorithms",)
        ).fetchone()

    assert ref is not None
    assert ref["kind"] == "ref"
    assert ref["url"] == "https://cp-algorithms.com/graph/breadth-first-search.html"
    topic = db.execute(
        "SELECT * FROM topics WHERE title = ?",
        ("BFS",)
    ).fetchone()
    assert topic is not None

def test_admin_creates_problem_and_solution(admin_client):

    response = admin_client.post(
        "/admin/topics/new",
        data={
            "title": "Grafos",
            "summary": "Estudo de grafos",
            "level": "nivel_1",

            "new_problem_title": [
                "BFS"
            ],

            "new_problem_url": [
                "https://example.com"
            ],

            "new_problem_difficulty": [
                "medium"
            ],

            "new_problem_statement": [
                "Dado um grafo, encontre a menor distância."
            ],

            "new_problem_explanation": [
                "Usamos busca em largura porque explora os vértices por níveis."
            ],

            "new_problem_code": [
                "queue<int> q;"
            ]
        }
    )

    assert response.status_code == 302

    with flask_app.get_db() as db:

        topic = db.execute(
            """
            SELECT *
            FROM topics
            WHERE title = ?
            """,
            ("Grafos",)
        ).fetchone()

        problem = db.execute(
            """
            SELECT *
            FROM topic_items
            WHERE title = ?
            """,
            ("BFS",)
        ).fetchone()

        solution = db.execute(
            """
            SELECT *
            FROM problem_solutions
            WHERE item_id = ?
            """,
            (problem["id"],)
        ).fetchone()

    assert topic is not None
    assert topic["title"] == "Grafos"
    assert topic["summary"] == "Estudo de grafos"

    assert problem is not None
    assert problem["kind"] == "problem"
    assert problem["title"] == "BFS"
    assert problem["url"] == "https://example.com"
    assert problem["difficulty"] == "medium"
    assert problem["topic_id"] == topic["id"]

    assert solution is not None
    assert solution["item_id"] == problem["id"]
    assert solution["statement"] == "Dado um grafo, encontre a menor distância."
    assert solution["explanation"] == (
        "Usamos busca em largura porque explora os vértices por níveis."
    )
    assert solution["code"] == "queue<int> q;"

def test_admin_cannot_create_topic_without_title(admin_client):

    response = admin_client.post(
        "/admin/topics/new",
        data={
            "summary": "Sem título",
            "level": "nivel_1"
        }
    )

    assert response.status_code == 400