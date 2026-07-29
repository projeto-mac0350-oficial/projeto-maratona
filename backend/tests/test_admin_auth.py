import app as flask_app

# ------------- /admin --------------------------------
def test_admin_can_login(admin_client):
    response = admin_client.get("/me")

    assert response.status_code == 200
    data = response.get_json()

    assert data["username"] == "admin"
    assert data["is_admin"] is True

def test_admin_requires_login(client):
    response = client.get("/admin")

    assert response.status_code == 401

def test_normal_user_cannot_access_admin(auth_client):
    response = auth_client.get("/admin")

    assert response.status_code == 403

def test_admin_can_access_admin_page(admin_client):
    response = admin_client.get("/admin")

    assert response.status_code == 200