import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fu7ur3pr00f.api.config import settings

from fu7ur3pr00f.memory.knowledge import get_knowledge_store
from fu7ur3pr00f.memory.episodic import get_episodic_store
from fu7ur3pr00f.memory.profile import load_profile

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("fu7ur3pr00f.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing persistent state stores...")
    try:
        app.state.career_knowledge_store = get_knowledge_store()
        app.state.episodic_store = get_episodic_store()
        app.state.user_profile = load_profile()
        logger.info("Application state components successfully loaded.")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize application state: {e}")
        raise
    finally:
        logger.info("Tearing down API layer instances and releasing resources...")

app = FastAPI(title="fu7ur3pr00f API", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health", tags=["Monitoring"])
async def get_health():
    return {"status": "ok", "version": "0.3.0"}