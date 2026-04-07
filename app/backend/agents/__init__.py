"""
Agents module for DevOps Days CORP demo.

CONFIGURATION:
- SEARCH_ENDPOINT: Azure AI Search endpoint (ver config.py)
- MODEL: gpt-4o
- Índices: index-politicas, index-runbooks, index-herramientas
"""

# KB-grounded agents
from .politicas_agent import run_politicas_agent, POLITICAS_INSTRUCTIONS
from .runbooks_agent import run_runbooks_agent, RUNBOOKS_INSTRUCTIONS
from .herramientas_agent import run_herramientas_agent, HERRAMIENTAS_INSTRUCTIONS

# Orchestrator
from .orchestrator import run_orchestrator, run_single_query

__all__ = [
    # KB agents
    "run_politicas_agent",
    "run_runbooks_agent",
    "run_herramientas_agent",
    "POLITICAS_INSTRUCTIONS",
    "RUNBOOKS_INSTRUCTIONS",
    "HERRAMIENTAS_INSTRUCTIONS",
    # Orchestrator
    "run_orchestrator",
    "run_single_query",
]
