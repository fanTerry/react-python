def test_register_and_login(client):
    reg = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "123456", "email": "a@test.com"},
    )
    assert reg.json()["code"] == 0
    assert "access_token" in reg.json()["data"]

    login = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "123456"},
    )
    assert login.json()["code"] == 0
    assert login.json()["data"]["user"]["username"] == "alice"


def test_login_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"username": "bob", "password": "123456"},
    )
    res = client.post(
        "/api/auth/login",
        json={"username": "bob", "password": "wrong"},
    )
    assert res.json()["code"] == 401


def test_me_requires_auth(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_with_token(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.json()["code"] == 0
    assert res.json()["data"]["username"] == "tester"
