from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import ask_router
from core.storage.postgres_client import init_basic_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Modern FastAPI startup/shutdown handling.
    Runs once when the app starts and once when it stops.
    """

    # ---- STARTUP ----
    try:
        init_basic_schema()
        print("✅ Postgres tables initialized successfully.")
    except Exception as e:
        print("⚠️ [WARN] Failed to initialize Postgres schema:", e)

    yield  # <-- Application runs while yielded

    # ---- SHUTDOWN ----
    print("🛑 API shutting down...")


app = FastAPI(
    title="Enterprise RAG API",
    version="1.0.0",
    lifespan=lifespan,
)


# CORS middleware — required for Streamlit UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """
    Basic endpoint to check if the API is alive.
    """
    return {"status": "ok"}


# ---- Register Routers ----
app.include_router(ask_router.router)
