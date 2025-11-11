from fastapi import Header, HTTPException


async def auth_user(authorization: str | None = Header(default=None)):
    return {"user_id": "demo", "tenant_id": "demo", "principals": ["user"]}