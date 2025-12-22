from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.api.app.routers import (
    ask_router,
    upload,
    files,
    analysis,
    code_chat,
)

from services.api.app.auth.routes import router as auth_router
from services.api.app.routers.chat import router as chat_router





# ✅ FIXED IMPORT
from core.storage.postgres_client import init_all_schemas


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize ALL schemas on startup.
    """
    try:
        init_all_schemas()
        print("✅ Postgres schemas initialized successfully.")
    except Exception as e:
        print("⚠️ [WARN] Failed to initialize Postgres schema:", e)

    yield

    print("🛑 API shutting down...")


app = FastAPI(
    title="Enterprise RAG API",
    version="1.0.0",
    lifespan=lifespan
)

# ------------------------
# CORS
# ------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------
# ROUTERS
# ------------------------
app.include_router(upload.router)
app.include_router(ask_router.router)
app.include_router(files.router)
app.include_router(analysis.router)
app.include_router(code_chat.router)
app.include_router(auth_router)
app.include_router(chat_router)




@app.get("/health")
def health():
    return {"status": "ok"}
