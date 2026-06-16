from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

import blog_db as db
from deps import get_current_user
from response import ApiResponse, fail, ok

router = APIRouter(prefix="/api/posts", tags=["posts"])


class PostCreate(BaseModel):
    title: str
    content: str = ""
    category_name: Optional[str] = None
    tag_names: list[str] = []


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_name: Optional[str] = None
    tag_names: Optional[list[str]] = None


@router.get("/meta/categories", response_model=ApiResponse)
def list_categories():
    return ok(db.list_categories())


@router.get("/meta/tags", response_model=ApiResponse)
def list_tags():
    return ok(db.list_tags())


@router.get("", response_model=ApiResponse)
def list_posts(
    q: str = Query("", max_length=100),
    category_id: str = Query(""),
    tag_id: str = Query(""),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    return ok(
        db.list_posts(
            q=q,
            category_id=category_id,
            tag_id=tag_id,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/{post_id}", response_model=ApiResponse)
def get_post(post_id: str):
    post = db.get_post(post_id)
    if post is None:
        return fail(404, "Post not found")
    return ok(post)


@router.post("", response_model=ApiResponse)
def create_post(
    body: PostCreate,
    current_user: dict = Depends(get_current_user),
):
    post = db.create_post(
        body.title,
        body.content,
        category_name=body.category_name,
        tag_names=body.tag_names,
        author_id=current_user["id"],
    )
    return ok(post, message="发布成功")


@router.patch("/{post_id}", response_model=ApiResponse)
def update_post(
    post_id: str,
    body: PostUpdate,
    current_user: dict = Depends(get_current_user),
):
    post = db.get_post(post_id)
    if post is None:
        return fail(404, "Post not found")
    if post.get("author") and post["author"]["id"] != current_user["id"]:
        return fail(403, "只能编辑自己的文章")

    fields = body.model_fields_set
    updated = db.update_post(
        post_id,
        title=body.title,
        content=body.content,
        category_name=body.category_name,
        tag_names=body.tag_names,
        category_set="category_name" in fields,
        tags_set="tag_names" in fields,
    )
    return ok(updated, message="更新成功")


@router.delete("/{post_id}", response_model=ApiResponse)
def delete_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
):
    post = db.get_post(post_id)
    if post is None:
        return fail(404, "Post not found")
    if post.get("author") and post["author"]["id"] != current_user["id"]:
        return fail(403, "只能删除自己的文章")
    if not db.delete_post(post_id):
        return fail(404, "Post not found")
    return ok(message="删除成功")
