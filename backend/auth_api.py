from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

import auth_db
import blog_db as db
from deps import create_access_token, get_current_user
from response import ApiResponse, fail, ok

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterBody(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=64)
    email: Optional[str] = None


class LoginBody(BaseModel):
    username: str
    password: str


@router.post("/register", response_model=ApiResponse)
def register(body: RegisterBody):
    if auth_db.get_user_by_username(body.username):
        return fail(400, "用户名已存在")
    user = auth_db.create_user(body.username, body.password, body.email)
    token = create_access_token(user["id"])
    return ok({"access_token": token, "user": user}, message="注册成功")


@router.post("/login", response_model=ApiResponse)
def login(body: LoginBody):
    user = auth_db.authenticate_user(body.username, body.password)
    if user is None:
        return fail(401, "用户名或密码错误")
    token = create_access_token(user["id"])
    return ok({"access_token": token, "user": user}, message="登录成功")


@router.get("/me", response_model=ApiResponse)
def me(current_user: dict = Depends(get_current_user)):
    return ok(current_user)


@router.get("/profile", response_model=ApiResponse)
def profile(
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    posts = db.list_posts(
        author_id=current_user["id"],
        page=page,
        page_size=page_size,
    )
    return ok(
        {
            "user": current_user,
            "post_count": posts["total"],
            "posts": posts,
        }
    )
