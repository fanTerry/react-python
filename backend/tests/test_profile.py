def test_profile_requires_auth(client):
    res = client.get("/api/auth/profile")
    assert res.status_code == 401


def test_profile_with_posts(client, auth_headers):
    client.post(
        "/api/posts",
        json={"title": "我的第一篇文章", "content": "内容"},
        headers=auth_headers,
    )
    client.post(
        "/api/posts",
        json={"title": "第二篇", "content": ""},
        headers=auth_headers,
    )

    res = client.get("/api/auth/profile", headers=auth_headers)
    data = res.json()["data"]
    assert data["user"]["username"] == "tester"
    assert data["post_count"] == 2
    assert len(data["posts"]["items"]) == 2
    assert data["posts"]["items"][0]["title"] == "第二篇"
