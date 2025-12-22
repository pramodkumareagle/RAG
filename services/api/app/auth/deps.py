from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from core.storage.postgres_client import execute
from services.api.app.auth.jwt import decode_access_token

# ✅ THIS IS THE KEY LINE
pwd_context = CryptContext(
    schemes=["bcrypt_sha256"],
    deprecated="auto"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def get_current_user(token: str = Depends(oauth2_scheme)):
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = execute("SELECT * FROM users WHERE id=%s", (user_id,))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user[0]
