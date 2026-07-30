""" Tests for user goals """

import app as flask_app
# ------------ GET /goals -------------------

def test_list_goals_empty(auth_client):
    response = auth_client.get("/goals")
    assert response.status_code == 200
    assert response.get_json() == []

def test_list_goals_requires_login(client):
    response = client.get("/goals")
    assert response.status_code == 401

def test_list_goals(auth_client):
    auth_client.post("/goals",json={"description": "Estudar grafos"})
    response = auth_client.get("/goals")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["description"] == "Estudar grafos"

def test_list_goals_keep_creation_order(auth_client):
    for goal in ["Estudar", "Praticar", "Revisar"]:
        auth_client.post("/goals", json={"description": goal})
    data = auth_client.get("/goals").get_json()
    assert [g["description"] for g in data] == ["Estudar","Praticar","Revisar"]

def test_list_goals_does_not_show_other_users_goals(auth_client):
    auth_client.post("/goals", json={"description": "Meta da Alice"})
    other = flask_app.app.test_client()
    other.post("/register", json={"username": "bob","password": "123"})
    other.post("/login", json={"username": "bob","password": "123"})
   
    response = other.get("/goals")
    assert response.get_json() == []
    response = auth_client.get("/goals")
    goals = response.get_json()
    assert len(goals) == 1
    assert goals[0]["description"] == "Meta da Alice"

# ------------ POST /goals ------------------------------------

def test_create_goal(auth_client):
    response = auth_client.post("/goals",json={"description": "Estudar DP"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["description"] == "Estudar DP"
    assert data["due_day"] is None
    assert data["due_month"] is None

def test_create_goal_with_due_date(auth_client):
    response = auth_client.post("/goals",json={"description": "Fazer simulado","due_day": 15,"due_month": 8})
    assert response.status_code == 201
    data = response.get_json()
    assert data["due_day"] == 15
    assert data["due_month"] == 8

def test_create_goal_requires_description(auth_client):
    response = auth_client.post("/goals",json={})
    assert response.status_code == 400

def test_create_goal_rejects_long_description(auth_client):
    response = auth_client.post("/goals",json={"description": "a" * 101})
    assert response.status_code == 400

def test_create_goal_requires_complete_due_date(auth_client):
    response = auth_client.post("/goals",json={"description": "Estudar","due_day": 10})
    assert response.status_code == 400

def test_create_goal_rejects_invalid_date(auth_client):
    response = auth_client.post("/goals",json={"description": "Estudar","due_day": 40,"due_month": 13})
    assert response.status_code == 400

def test_create_goal_requires_login(client):
    response = client.post("/goals",json={"description": "Estudar"})
    assert response.status_code == 401

# ----------- DELETE /goals/<int:goal_id> -----------------------

def test_delete_goal_requires_login(client):
    response = client.delete("/goals/1")
    assert response.status_code in (401, 302)

def test_delete_goal(auth_client):
    response = auth_client.post("/goals", json={"description": "Estudar DP"})
    goal_id = response.get_json()["id"]
    response = auth_client.delete(f"/goals/{goal_id}")
    assert response.status_code == 200
    assert response.get_json() == {"deleted": True}
    goals = auth_client.get("/goals").get_json()
    assert all(goal["id"] != goal_id for goal in goals)

def test_user_cannot_delete_other_users_goal(auth_client):
    response = auth_client.post("/goals", json={"description": "Study Flask"})
    goal_id = response.get_json()["id"]
   
    other = flask_app.app.test_client()
    other.post("/register", json={"username": "b", "password": "x"})
    other.post("/login", json={"username": "b", "password": "x"})

    response = other.delete(f"/goals/{goal_id}")

    goals = auth_client.get("/goals").get_json()
    assert any(goal["id"] == goal_id for goal in goals)

