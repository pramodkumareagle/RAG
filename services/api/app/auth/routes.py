from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
import uuid

from core.storage.postgres_client import execute
from services.api.app.auth.deps import hash_password, verify_password
from services.api.app.auth.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


@router.post("/register")
def register(data: RegisterRequest):
    # 🔒 bytes check (bcrypt cares about BYTES)
    if len(data.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password must be 72 bytes or less")

    existing = execute("SELECT id FROM users WHERE email=%s", (data.email,))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    execute(
        "INSERT INTO users (id, email, hashed_password, full_name) VALUES (%s, %s, %s, %s)",
        (user_id, data.email, hash_password(data.password), data.full_name),
    )

    return {"access_token": create_access_token(user_id), "token_type": "bearer"}


@router.post("/login")
def login(data: LoginRequest):
    if len(data.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password must be 72 bytes or less")

    user = execute("SELECT * FROM users WHERE email=%s", (data.email,))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, user[0]["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"access_token": create_access_token(str(user[0]["id"])), "token_type": "bearer"}
