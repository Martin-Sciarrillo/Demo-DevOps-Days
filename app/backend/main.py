"""
FoundryIQ and Agent Framework Demo Backend

Simple FastAPI wrapper around the orchestrator.
"""

import os
import sys
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
        # Lazy import to avoid startup hang
        from agents.orchestrator import run_single_query
        
        route, response_text, sources = await run_single_query(request.message)
        
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
                "id": "hr",
                "name": "HR Agent",
                "description": "Handles HR policies, PTO, benefits, and employee handbook queries",
                "kb": "kb1-hr",
                "color": "#8B5CF6",
            },
            {
                "id": "marketing",
                "name": "Marketing Agent",
                "description": "Handles marketing campaigns, brand, and competitor analysis",
                "kb": "kb2-marketing",
                "color": "#EC4899",
            },
            {
                "id": "products",
                "name": "Products Agent",
                "description": "Handles product catalog, features, and specifications",
                "kb": "kb3-products",
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
