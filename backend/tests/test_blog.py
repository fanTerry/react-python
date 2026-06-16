def test_list_posts_empty(client):
    res = client.get("/api/posts")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["items"] == []
    assert data["total"] == 0


def test_create_post_requires_auth(client):
    res = client.post(
        "/api/posts",
        json={"title": "无权限", "content": ""},
    )
    assert res.status_code == 401


def test_create_and_get_post(client, auth_headers):
    create_res = client.post(
        "/api/posts",
        json={
            "title": "第一篇博客",
            "content": "# Hello\n\nMarkdown",
            "category_name": "技术",
            "tag_names": ["Python", "FastAPI"],
        },
        headers=auth_headers,
    )
    post = create_res.json()["data"]
    assert post["title"] == "第一篇博客"
    assert post["category"]["name"] == "技术"
    assert len(post["tags"]) == 2
    assert post["author"]["username"] == "tester"

    get_res = client.get(f"/api/posts/{post['id']}")
    assert get_res.json()["data"]["title"] == "第一篇博客"


def test_update_post(client, auth_headers):
    post_id = client.post(
        "/api/posts",
        json={"title": "旧标题", "content": "旧内容"},
        headers=auth_headers,
    ).json()["data"]["id"]

    res = client.patch(
        f"/api/posts/{post_id}",
        json={"title": "新标题", "category_name": "生活", "tag_names": ["日记"]},
        headers=auth_headers,
    )
    data = res.json()["data"]
    assert data["title"] == "新标题"
    assert data["category"]["name"] == "生活"
    assert data["tags"][0]["name"] == "日记"


def test_delete_post(client, auth_headers):
    post_id = client.post(
        "/api/posts",
        json={"title": "待删", "content": ""},
        headers=auth_headers,
    ).json()["data"]["id"]

    client.delete(f"/api/posts/{post_id}", headers=auth_headers)
    assert client.get("/api/posts").json()["data"]["total"] == 0


def test_search_and_filter(client, auth_headers):
    client.post(
        "/api/posts",
        json={"title": "Python 入门", "content": "FastAPI", "category_name": "技术", "tag_names": ["Python"]},
        headers=auth_headers,
    )
    client.post(
        "/api/posts",
        json={"title": "React 笔记", "content": "组件", "category_name": "前端", "tag_names": ["React"]},
        headers=auth_headers,
    )

    search = client.get("/api/posts", params={"q": "Python"}).json()["data"]
    assert search["total"] == 1

    cats = client.get("/api/posts/meta/categories").json()["data"]
    tech = next(c for c in cats if c["name"] == "技术")
    filtered = client.get("/api/posts", params={"category_id": tech["id"]}).json()["data"]
    assert filtered["total"] == 1
    assert filtered["items"][0]["title"] == "Python 入门"


def test_post_pagination(client, auth_headers):
    for i in range(4):
        client.post(
            "/api/posts",
            json={"title": f"文章{i}", "content": ""},
            headers=auth_headers,
        )

    page1 = client.get("/api/posts", params={"page": 1, "page_size": 3}).json()["data"]
    assert page1["total"] == 4
    assert len(page1["items"]) == 3
