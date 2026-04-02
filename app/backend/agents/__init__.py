"""
Agents module for DevOps Days CORP demo.

CONFIGURATION:
- SEARCH_ENDPOINT: Azure AI Search endpoint (ver config.py)
- MODEL: gpt-4o
- Índices: index-politicas, index-runbooks, index-herramientas
"""

# KB-grounded agents
from .politicas_agent import run_hr_agent, HR_INSTRUCTIONS
from .runbooks_agent import run_marketing_agent, MARKETING_INSTRUCTIONS
from .herramientas_agent import run_products_agent, PRODUCTS_INSTRUCTIONS

# Orchestrator
from .orchestrator import run_orchestrator, run_single_query

__all__ = [
    # KB agents
    "run_hr_agent",
    "run_marketing_agent",
    "run_products_agent",
    "HR_INSTRUCTIONS",
    "MARKETING_INSTRUCTIONS",
    "PRODUCTS_INSTRUCTIONS",
    # Orchestrator
    "run_orchestrator",
    "run_single_query",
]
