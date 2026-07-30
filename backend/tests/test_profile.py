""" Tests for the profile page """

def test_profile_page_loads(auth_client):
    response = auth_client.get("/perfil")
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")

def test_profile_requires_login(client):
    response = client.get("/perfil")
    assert response.status_code == 401

def test_admin_profile_page_loads(admin_client):
    response = admin_client.get("/perfil")
    assert response.status_code == 200
    assert b"profile" in response.data