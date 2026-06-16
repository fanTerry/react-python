import os
from datetime import timedelta

JWT_SECRET = os.environ.get(
    "JWT_SECRET", "dev-secret-key-at-least-32-bytes-long!!"
)
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "1440"))

ACCESS_TOKEN_EXPIRE = timedelta(minutes=JWT_EXPIRE_MINUTES)
