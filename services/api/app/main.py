from fastapi import FastAPI
from app.auth import auth_user
from fastapi import Depends

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}