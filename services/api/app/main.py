# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ask_router, upload, files
from core.storage.postgres_client import init_basic_schema, init_table_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize schemas on startup and log shutdown.
    """
    try:
        init_basic_schema()
        init_table_schema()
        print("✅ Postgres tables initialized successfully.")
    except Exception as e:
        print("⚠️ [WARN] Failed to initialize Postgres schema:", e)

    yield

    print("🛑 API shutting down...")


app = FastAPI(title="Enterprise RAG API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(ask_router.router)
app.include_router(files.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def startup():
    init_basic_schema()
    init_table_schema()
    print("✅ Postgres tables initialized successfully.")


