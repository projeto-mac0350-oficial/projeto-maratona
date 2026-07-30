""" Tests for the solution page """

# ------- GET /solucao ----------------------
def test_solution_page_loads(client):
    response = client.get("/solucao")
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")


# ------- GET /solutions/<slug> ---------------------
def test_get_solution_returns_problem_solution(admin_client, client):

    admin_client.post(
        "/admin/topics/new",
        data={
            "title": "Grafos",
            "summary": "Estudo de grafos",
            "level": "nivel_1",
            "new_problem_title": ["BFS"],
            "new_problem_url": ["https://example.com/bfs"],
            "new_problem_difficulty": ["medium"],
            "new_problem_statement": ["Encontre o caminho mínimo."],
            "new_problem_explanation": ["Usa busca em largura."],
            "new_problem_code": ["queue<int> q;"]
        }
    )

    response = client.get("/solutions/bfs")

    assert response.status_code == 200

    data = response.get_json()

    assert data["title"] == "BFS"
    assert data["url"] == "https://example.com/bfs"
    assert data["statement"] == "Encontre o caminho mínimo."
    assert data["explanation"] == "Usa busca em largura."
    assert data["code"] == "queue<int> q;"
    assert data["topic_slug"] == "grafos"

def test_get_unknown_solution_is_404(client):
    response = client.get("/solutions/not-exist")
    assert response.status_code == 404