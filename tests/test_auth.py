def test_register(auth_client):
    response = auth_client.post("/librarian/register", json={
        "email": "new_useer@example.com",
        "password": "newpass"
    })
    assert response.status_code == 200

def test_protected_route(auth_client):
    response = auth_client.get("/books")
    assert response.status_code == 200

def test_unauthenticated_access(client):
    response = client.get("/books")
    assert response.status_code == 401