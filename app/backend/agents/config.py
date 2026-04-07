"""Shared configuration for all agents. Values come from environment variables."""

import os

OPENAI_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT",
    "https://cog-jnlr3ry4yf2o6.openai.azure.com/",
)

SEARCH_ENDPOINT = os.getenv(
    "AZURE_SEARCH_ENDPOINT",
    "https://srch-jnlr3ry4yf2o6.search.windows.net",
)

MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

INDEX_POLITICAS = "index-politicas"
INDEX_RUNBOOKS = "index-runbooks"
INDEX_HERRAMIENTAS = "index-herramientas"

# FoundryIQ Agentic Retrieval — Knowledge Base names
KB_POLITICAS = "kb-politicas"
KB_RUNBOOKS = "kb-runbooks"
KB_HERRAMIENTAS = "kb-herramientas"
