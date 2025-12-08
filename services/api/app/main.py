from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# FIXED IMPORTS
from services.api.app.routers import ask_router, upload, files, analysis
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


app = FastAPI(
    title="Enterprise RAG API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(upload.router)
app.include_router(ask_router.router)
app.include_router(files.router)
app.include_router(analysis.router)


@app.get("/health")
def health():
    return {"status": "ok"}
