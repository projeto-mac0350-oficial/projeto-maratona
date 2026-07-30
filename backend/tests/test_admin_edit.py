""" Tests for updating topics through the admin panel """
import app as flask_app

# -------- POST /admin/topics/<slug>/edit ----------------------

def test_admin_updates_topic(admin_client):

    admin_client.post(
        "/admin/topics/new",
        data={
            "title": "Grafos",
            "summary": "Resumo antigo",
            "level": "nivel_1",
        }
    )

    response = admin_client.post(
        "/admin/topics/grafos/edit",
        data={
            "title": "Grafos Avançados",
            "summary": "Resumo atualizado",
            "level": "nivel_2",
            "problem_id": [],
            "problem_title": [],
            "problem_url": [],
            "problem_difficulty": [],
            "problem_statement": [],
            "problem_explanation": [],
            "problem_code": [],
            "new_problem_title": [],
            "new_problem_url": [],
            "new_problem_difficulty": [],
            "new_problem_statement": [],
            "new_problem_explanation": [],
            "new_problem_code": [],
            "new_ref_title": [],
            "new_ref_url": [],
        }
    )

    assert response.status_code == 302

    with flask_app.get_db() as db:

        topic = db.execute(
            """
            SELECT *
            FROM topics
            WHERE slug = ?
            """,
            ("grafos",)
        ).fetchone()

    assert topic is not None
    assert topic["title"] == "Grafos Avançados"
    assert topic["summary"] == "Resumo atualizado"

    level = None
    with flask_app.get_db() as db:
        level = db.execute(
            """
            SELECT title
            FROM levels
            WHERE id = ?
            """,
            (topic["level_id"],)
        ).fetchone()

    assert level["title"] == "Programação 1"