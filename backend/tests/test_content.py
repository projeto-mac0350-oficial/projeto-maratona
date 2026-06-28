"""Tests for the study-content model and its read-only API.

Content (topics, their references and problems) is seeded into the database by
init_db(), so the test client — which runs init_db() against a throwaway DB —
sees the same content the app serves.
"""


# --- GET /topics -----------------------------------------------------------


def test_list_topics_includes_busca_binaria(client):
    res = client.get("/topics")
    assert res.status_code == 200
    topics = res.get_json()
    assert isinstance(topics, list)
    bb = next((t for t in topics if t["slug"] == "busca_binaria"), None)
    assert bb is not None
    assert bb["title"] == "Busca Binária"
    assert bb["summary"]  # non-empty description


def test_list_topics_does_not_leak_items(client):
    """The list view is a summary; full refs/problems live on the detail route."""
    bb = next(t for t in client.get("/topics").get_json() if t["slug"] == "busca_binaria")
    assert "problems" not in bb
    assert "references" not in bb


# --- GET /topics/<slug> ----------------------------------------------------


def test_get_topic_returns_references_and_problems(client):
    res = client.get("/topics/busca_binaria")
    assert res.status_code == 200
    data = res.get_json()
    assert data["slug"] == "busca_binaria"
    assert data["title"] == "Busca Binária"

    ref_keys = [r["item_key"] for r in data["references"]]
    assert "busca_binaria:ref:cp-algorithms" in ref_keys

    prob_keys = [p["item_key"] for p in data["problems"]]
    assert "busca_binaria:prob:roadworks" in prob_keys


def test_get_topic_problem_has_links_and_label(client):
    data = client.get("/topics/busca_binaria").get_json()
    roadworks = next(p for p in data["problems"] if p["slug"] == "roadworks")
    assert roadworks["kind"] == "problem"
    assert roadworks["url"]            # problem statement link
    assert roadworks["solution_url"]   # solution link
    assert roadworks["label"] == "Problema 1 - Roadworks"


def test_get_topic_reference_label_is_the_title(client):
    data = client.get("/topics/busca_binaria").get_json()
    cp = next(r for r in data["references"] if r["slug"] == "cp-algorithms")
    assert cp["kind"] == "ref"
    assert cp["label"] == "CP-Algorithms"


def test_get_topic_items_keep_authoring_order(client):
    data = client.get("/topics/busca_binaria").get_json()
    assert [p["slug"] for p in data["problems"]] == ["roadworks", "nome-2", "nome-3"]


def test_get_unknown_topic_is_404(client):
    assert client.get("/topics/does-not-exist").status_code == 404


# --- content keys line up with the progress API ----------------------------


def test_content_item_keys_match_progress_storage(auth_client):
    """A problem's item_key from the content API is the very key /progress uses,
    so toggling it on a content page and reading it back stay in sync."""
    data = auth_client.get("/topics/busca_binaria").get_json()
    problem = data["problems"][0]
    auth_client.post(
        "/progress",
        json={
            "item_key": problem["item_key"],
            "kind": problem["kind"],
            "label": problem["label"],
            "done": True,
        },
    )
    saved = auth_client.get("/progress").get_json()
    assert saved[problem["item_key"]]["done"] is True
