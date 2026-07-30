""" Tests for the study-content model """

import app as flask_app

# --- GET /topics -----------------------------------------------------------

def test_list_topics(admin_client,client):

    admin_client.post(
        "/admin/topics/new",
        data={
            "title": "Test Topic",
            "summary": "Test summary",
            "level": "nivel_1"
        }
    )
    response = client.get("/topics")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "slug" in data[0]
    assert "title" in data[0]
    assert "summary" in data[0]

def test_list_topics_does_not_leak_items(admin_client, client):
    """The list view is a summary; full refs/problems live on the detail route."""

    admin_client.post(
        "/admin/topics/new",
        data={
            "title": "Test Topic",
            "summary": "Test summary",
            "level": "nivel_1",

            "new_ref_title": [
                "Test Reference"
            ],

            "new_ref_url": [
                "https://example.com/reference"
            ]
        }
    )

    with flask_app.get_db() as db:
        topic = db.execute(
            """
            SELECT *
            FROM topics
            WHERE title = ?
            """,
            ("Test Topic",)
        ).fetchone()

    assert topic is not None

    topics = client.get("/topics").get_json()

    created_topic = next(
        t for t in topics
        if t["slug"] == topic["slug"]
    )

    assert "problems" not in created_topic
    assert "references" not in created_topic

# --- GET /topics/<slug> ----------------------------------------------------

def test_get_topic_returns_references_and_problems(admin_client, client):

    admin_client.post(
        "/admin/topics/new",
        data={
            "title": "Test Topic",
            "summary": "Test summary",
            "level": "nivel_1",
            "new_ref_title": [ "CP Algorithms"],
            "new_ref_url": [ "https://example.com/cp-algorithms"],
            "new_problem_title": [ "Roadworks"],
            "new_problem_url": [ "https://example.com/roadworks"],
            "new_problem_difficulty": [ "easy"],
            "new_problem_statement": [ "Solve this problem"],
            "new_problem_explanation": ["Explanation"],
            "new_problem_code": ["int main() {}"]
        }
    )

    with flask_app.get_db() as db:
        topic = db.execute(
            """
            SELECT *
            FROM topics
            WHERE title = ?
            """,
            ("Test Topic",)
        ).fetchone()

    assert topic is not None

    res = client.get(f"/topics/{topic['slug']}")
    assert res.status_code == 200

    data = res.get_json()
    print(data)
    assert data["slug"] == topic["slug"]
    assert data["title"] == "Test Topic"

    ref_keys = [r["item_key"] for r in data["references"]]
    assert "test-topic:ref:cp-algorithms" in ref_keys

    prob_keys = [p["item_key"] for p in data["problems"]]
    assert "test-topic:prob:roadworks" in prob_keys

def test_get_topic_items_keep_authoring_order(admin_client, client):

    admin_client.post(
        "/admin/topics/new",
        data={
            "title": "Test Topic",
            "summary": "summary",
            "level": "nivel_1",
            "new_problem_title": ["Problem A", "Problem B", "Problem C"],
            "new_problem_url": ["a.com", "b.com", "c.com"],
            "new_problem_difficulty": ["easy", "medium", "hard"],
            "new_problem_statement": ["A", "B", "C"],
            "new_problem_explanation": ["A", "B", "C"],
            "new_problem_code": ["A", "B", "C"]
        }
    )

    with flask_app.get_db() as db:
        topic = db.execute(
            "SELECT slug FROM topics WHERE title = ?",
            ("Test Topic",)
        ).fetchone()

    data = client.get(f"/topics/{topic['slug']}").get_json()

    assert [p["slug"] for p in data["problems"]] == ["problem-a","problem-b","problem-c"]

def test_get_unknown_topic_is_404(client):
    assert client.get("/topics/does-not-exist").status_code == 404


# --- difficulty ------------------------------------------------------------

def test_problems_expose_their_difficulty(admin_client, client):

    admin_client.post(
        "/admin/topics/new",
        data={
            "title": "Test Topic",
            "summary": "summary",
            "level": "nivel_1",
            "new_problem_title": ["Easy Problem", "Medium Problem", "Hard Problem"],
            "new_problem_url": ["easy.com", "medium.com", "hard.com"],
            "new_problem_difficulty": ["easy", "medium", "hard"],
            "new_problem_statement": ["A", "B", "C"],
            "new_problem_explanation": ["A", "B", "C"],
            "new_problem_code": ["A", "B", "C"]
        }
    )

    with flask_app.get_db() as db:
        topic = db.execute(
            "SELECT slug FROM topics WHERE title = ?",
            ("Test Topic",)
        ).fetchone()

    data = client.get(f"/topics/{topic['slug']}").get_json()

    by_slug = {p["slug"]: p for p in data["problems"]}

    assert by_slug["easy-problem"]["difficulty"] == "easy"
    assert by_slug["medium-problem"]["difficulty"] == "medium"
    assert by_slug["hard-problem"]["difficulty"] == "hard"

def test_references_have_no_difficulty(admin_client, client):

    admin_client.post(
        "/admin/topics/new",
        data={
            "title": "Test Topic",
            "summary": "summary",
            "level": "nivel_1",
            "new_ref_title": ["CP Algorithms"],
            "new_ref_url": ["cp.com"]
        }
    )

    with flask_app.get_db() as db:
        topic = db.execute(
            "SELECT slug FROM topics WHERE title = ?",
            ("Test Topic",)
        ).fetchone()

    data = client.get(f"/topics/{topic['slug']}").get_json()

    ref = data["references"][0]

    assert ref["kind"] == "ref"
    assert "difficulty" not in ref


# --- content keys line up with the progress API ----------------------------

def test_content_item_keys_match_progress_storage(admin_client):

    admin_client.post(
        "/admin/topics/new",
        data={
            "title": "Test Topic",
            "summary": "summary",
            "level": "nivel_1",
            "new_problem_title": ["Problem A"],
            "new_problem_url": ["a.com"],
            "new_problem_difficulty": ["easy"],
            "new_problem_statement": ["A"],
            "new_problem_explanation": ["A"],
            "new_problem_code": ["A"]
        }
    )

    with flask_app.get_db() as db:
        topic = db.execute(
            "SELECT slug FROM topics WHERE title = ?",
            ("Test Topic",)
        ).fetchone()

    data = admin_client.get(
        f"/topics/{topic['slug']}"
    ).get_json()

    problem = data["problems"][0]

    admin_client.post(
        "/progress",
        json={
            "item_key": problem["item_key"],
            "kind": problem["kind"],
            "label": problem["label"],
            "done": True,
        }
    )

    saved = admin_client.get("/progress").get_json()

    assert saved[problem["item_key"]]["done"] is True

# ---- content -----------------------------------------------
def test_conteudo_page_loads(client):
    response = client.get("/conteudo")
    assert response.status_code == 200
    assert b"topic" in response.data

def test_conteudos_page_loads(client):
    response = client.get("/conteudos")
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")
