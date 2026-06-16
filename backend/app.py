import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth_api import router as auth_router
from auth_db import init_users_db
from blog_api import router as posts_router
from blog_db import init_posts_db
from chat_api import router as chat_router
from chat_db import init_chat_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_users_db()
    init_posts_db()
    init_chat_db()
    yield


app = FastAPI(title="Blog API", lifespan=lifespan)

_cors_origins = os.environ.get(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:8080"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+):\d+",
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(posts_router)
app.include_router(chat_router)
