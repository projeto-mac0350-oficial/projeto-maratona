""" Tests for the levels endpoint """

# ---- GET /levels --------------------

def test_list_levels(client):
    response = client.get("/levels")

    assert response.status_code == 200

    data = response.get_json()

    assert isinstance(data, list)
    assert len(data) > 0

    assert "slug" in data[0]
    assert "title" in data[0]


# ----- GET /levels/<slug> -------------------

def test_get_level(client):
    response = client.get("/levels/nivel_1")

    assert response.status_code == 200
    data = response.get_json()
    assert data["slug"] == "nivel_1"
    assert "title" in data
    assert "topics" in data
    assert isinstance(data["topics"], list)

def test_get_invalid_level(client):
    response = client.get("/levels/nao_existe")
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "level not found"