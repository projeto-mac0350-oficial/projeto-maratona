""" Tests for listing and deleting content through the admin panel """
import app as flask_app

# ------ GET /admin/topics --------------------------

def test_admin_can_list_topics(admin_client):

    admin_client.post(
        "/admin/topics/new",
        data={
            "title": "Grafos",
            "summary": "Estudo de grafos",
            "level": "nivel_1",
        }
    )

    response = admin_client.get("/admin/topics")

    assert response.status_code == 200

    data = response.get_json()

    assert isinstance(data, list)
    assert len(data) > 0

    topic = next(
        (t for t in data if t["slug"] == "grafos"),
        None
    )

    assert topic is not None
    assert topic["title"] == "Grafos"
    assert topic["level"] == "Nível 1"

def test_normal_user_cannot_list_admin_topics(auth_client):
    response = auth_client.get("/admin/topics")
    assert response.status_code == 403

def test_anonymous_cannot_list_admin_topics(client):
    response = client.get("/admin/topics")
    assert response.status_code == 401

# ------- DELETE /admin/topics/<slug> ------------------

def test_admin_deletes_topic_and_dependencies(admin_client):

    admin_client.post(
        "/admin/topics/new",
        data={
            "title": "Grafos",
            "summary": "Estudo de grafos",
            "level": "nivel_1",

            "new_problem_title": ["BFS"],
            "new_problem_url": ["https://example.com/bfs"],
            "new_problem_difficulty": [  "medium"],
            "new_problem_statement": [ "Encontre o caminho mínimo."],
            "new_problem_explanation": ["Usa fila."],
            "new_problem_code": ["queue<int> q;"],
            "new_ref_title": ["CP Algorithms"],
            "new_ref_url": [ "https://example.com/cp"]
        }
    )

    with flask_app.get_db() as db:
        topic = db.execute(
            """
            SELECT *
            FROM topics
            WHERE slug = ?
            """,
            ("grafos",)
        ).fetchone()

        problem = db.execute(
            """
            SELECT *
            FROM topic_items
            WHERE title = ?
            """,
            ("BFS",)
        ).fetchone()


    assert topic is not None
    assert problem is not None

    response = admin_client.delete(
        "/admin/topics/grafos"
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "success": True
    }

    with flask_app.get_db() as db:

        topic = db.execute(
            """
            SELECT *
            FROM topics
            WHERE slug = ?
            """,
            ("grafos",)
        ).fetchone()

        item = db.execute(
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
            """
        ).fetchone()


    assert topic is None
    assert item is None
    assert solution is None

def test_normal_user_cannot_delete_topic(auth_client):
    response = auth_client.delete("/admin/topics/grafos")
    assert response.status_code == 403

def test_anonymous_cannot_delete_topic(client):
    response = client.delete("/admin/topics/grafos")
    assert response.status_code == 401

# ------------ DELETE /admin/problems/<int:problem_id ---------------------

def test_admin_deletes_problem_and_solution(admin_client):

    admin_client.post(
        "/admin/topics/new",
        data={
            "title": "Grafos",
            "summary": "Estudo de grafos",
            "level": "nivel_1",
            "new_problem_title": [ "BFS"],
            "new_problem_url": ["https://example.com/bfs"],
            "new_problem_difficulty": ["medium"],
            "new_problem_statement": ["Encontre o menor caminho." ],
            "new_problem_explanation": ["Usamos BFS."],
            "new_problem_code": ["queue<int> q;"]
        }
    )

    with flask_app.get_db() as db:
        problem = db.execute(
            """
            SELECT *
            FROM topic_items
            WHERE title = ?
            """,
            ("BFS",)
        ).fetchone()

    assert problem is not None

    problem_id = problem["id"]

    response = admin_client.delete(
        f"/admin/problems/{problem_id}"
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "success": True
    }

    with flask_app.get_db() as db:

        deleted_problem = db.execute(
            """
            SELECT *
            FROM topic_items
            WHERE id = ?
            """,
            (problem_id,)
        ).fetchone()

        deleted_solution = db.execute(
            """
            SELECT *
            FROM problem_solutions
            WHERE item_id = ?
            """,
            (problem_id,)
        ).fetchone()


    assert deleted_problem is None
    assert deleted_solution is None

def test_normal_user_cannot_delete_problem(auth_client):
    response = auth_client.delete(
        "/admin/problems/1"
    )
    assert response.status_code == 403


# ------ DELETE /admin/references/<int:ref_id> --------------------

def test_admin_deletes_reference(admin_client):

    admin_client.post(
        "/admin/topics/new",
        data={
            "title": "Grafos",
            "summary": "Estudo de grafos",
            "level": "nivel_1",
            "new_ref_title": ["CP Algorithms"],
            "new_ref_url": ["https://example.com/cp-algorithms"]
        }
    )

    with flask_app.get_db() as db:
        ref = db.execute(
            """
            SELECT *
            FROM topic_items
            WHERE title = ?
            AND kind = 'ref'
            """,
            ("CP Algorithms",)
        ).fetchone()

    assert ref is not None

    ref_id = ref["id"]

    response = admin_client.delete(
        f"/admin/references/{ref_id}"
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "success": True
    }

    with flask_app.get_db() as db:
        deleted_ref = db.execute(
            """
            SELECT *
            FROM topic_items
            WHERE id = ?
            """,
            (ref_id,)
        ).fetchone()


    assert deleted_ref is None

def test_normal_user_cannot_delete_reference(auth_client):
    response = auth_client.delete(
        "/admin/references/1"
    )
    assert response.status_code == 403