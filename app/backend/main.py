"""
FoundryIQ and Agent Framework Demo Backend

Simple FastAPI wrapper around the orchestrator.
"""

import os
import sys
import asyncio
import unicodedata
import re
import random
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load .env from repo root and add agents/ to path so 'config' module is findable
_root = Path(__file__).resolve().parents[2]
load_dotenv(_root / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent / "agents"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── Demo response cache ───────────────────────────────────────────────────────
_CACHE: dict[str, tuple[str, str, list]] = {}

# Preguntas de la demo — se pre-calientan al arrancar el servidor
_DEMO_QUESTIONS = [
    "¿Cuál es el proceso de postmortem blameless?",
    "¿Cómo resuelvo un CrashLoopBackOff en producción?",
    "¿Cómo accedo a Vault para gestionar secretos?",
]

def _normalize(q: str) -> str:
    """Lowercase + strip accents + colapsar espacios para matching robusto."""
    nfkd = unicodedata.normalize("NFKD", q.lower().strip())
    ascii_str = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", ascii_str)

async def _prewarm():
    """Ejecuta las preguntas de demo en background y cachea las respuestas."""
    from agents.orchestrator import run_single_query
    for q in _DEMO_QUESTIONS:
        key = _normalize(q)
        if key not in _CACHE:
            try:
                print(f"Pre-warming: {q[:50]}...")
                result = await run_single_query(q)
                _CACHE[key] = result
                print(f"  ✓ cacheado ({q[:40]})")
            except Exception as e:
                print(f"  ✗ error pre-warming '{q[:40]}': {e}")


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    agent: str | None = None


class ChatResponse(BaseModel):
    message: str
    agent: str
    sources: list[dict] = []


class HealthResponse(BaseModel):
    status: str
    version: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — initializes agents once at startup."""
    from agents.orchestrator import startup, shutdown
    print("Starting FoundryIQ Agent Framework Demo...")
    await startup()
    print("Agents ready.")
    # Pre-warm demo questions in background — no bloquea el arranque
    asyncio.create_task(_prewarm())
    yield
    await shutdown()
    print("Shutting down...")


app = FastAPI(
    title="FoundryIQ Agent Framework Demo",
    description="Multi-agent orchestration using Microsoft Agent Framework",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="0.1.0")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the multi-agent system.
    Uses the orchestrator to route and respond.
    """
    try:
        from agents.orchestrator import run_single_query

        key = _normalize(request.message)
        if key in _CACHE:
            await asyncio.sleep(random.uniform(1.5, 3.0))
            route, response_text, sources = _CACHE[key]
        else:
            route, response_text, sources = await run_single_query(request.message)
            _CACHE[key] = (route, response_text, sources)

        return ChatResponse(
            message=response_text,
            agent=f"{route}-agent",
            sources=sources,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents")
async def list_agents():
    """List available agents with their metadata."""
    return {
        "agents": [
            {
                "id": "orchestrator",
                "name": "Orchestrator",
                "description": "Routes requests to specialized agents based on query content",
                "color": "#6366F1",
            },
            {
                "id": "politicas",
                "name": "Agente Políticas",
                "description": "Políticas de on-call, guardia, SLA/SLO, postmortem y certificaciones",
                "kb": "index-politicas",
                "color": "#8B5CF6",
            },
            {
                "id": "runbooks",
                "name": "Agente Runbooks",
                "description": "Runbooks operacionales, playbooks de incidentes y troubleshooting paso a paso",
                "kb": "index-runbooks",
                "color": "#EC4899",
            },
            {
                "id": "herramientas",
                "name": "Agente Herramientas",
                "description": "Catálogo de herramientas internas: Kubernetes, Terraform, CI/CD, monitoring",
                "kb": "index-herramientas",
                "color": "#10B981",
            },
        ]
    }


# Mount static files for frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
