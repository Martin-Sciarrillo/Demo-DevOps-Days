# Instructions for Coding Agents

This file contains instructions for developers and AI coding agents working on the FoundryIQ and Agent Framework demo.

## Overall Code Layout

* **app/backend/agents/**: Python agents using Microsoft Agent Framework
  * `orchestrator.py`: Main orchestrator that routes requests to specialist agents
  * `politicas_agent.py`: Agente de Políticas (grounded to `kb-politicas`)
  * `runbooks_agent.py`: Agente de Runbooks (grounded to `kb-runbooks`)
  * `herramientas_agent.py`: Agente de Herramientas (grounded to `kb-herramientas`)
  * `config.py`: Shared configuration (endpoints, index names, KB names)
* **app/frontend/**: React frontend with TypeScript
* **infra/**: Bicep templates for Azure resources
* **scripts/**: Deployment and utility scripts
  * `setup_rbac.sh`: RBAC role assignments (required permissions)
  * `setup_openai_deployments.sh`: Model deployments (gpt-4o)
  * `setup_indexes.sh`: Create search indexes
  * `setup_foundry_devops.py`: Create FoundryIQ Knowledge Bases
  * `seed_indexes.py`: Populate indexes with demo documents

## Architecture

```
User Query
    ↓
Orchestrator (orchestrator.py)
    ↓ (routes based on query type)
    ├── Agente de Políticas (politicas_agent.py) → kb-politicas
    ├── Agente de Runbooks  (runbooks_agent.py)  → kb-runbooks
    └── Agente de Herramientas (herramientas_agent.py) → kb-herramientas
    ↓
Response
```

## Adding a New Agent

1. **Create agent file** in `app/backend/agents/`:
   ```python
   # nuevo_agente.py
   from agent_framework import Agent, Message, Content
   from agent_framework_openai import OpenAIChatCompletionClient
   from agent_framework.azure import AzureAISearchContextProvider
   from config import OPENAI_ENDPOINT, SEARCH_ENDPOINT, MODEL, INDEX_NUEVO

   NUEVO_INSTRUCTIONS = """Your instructions here..."""

   async def run_nuevo_agent(query: str) -> str:
       async with DefaultAzureCredential() as credential:
           client = OpenAIChatCompletionClient(...)
           async with AzureAISearchContextProvider("nuevo-search", ...) as kb_context:
               agent = Agent(client=client, context_providers=[kb_context], instructions=NUEVO_INSTRUCTIONS)
               response = await agent.run(Message(role="user", contents=[Content.from_text(query)]))
               return response.text
   ```

2. **Add index constant** in `config.py`:
   ```python
   INDEX_NUEVO = "index-nuevo"
   KB_NUEVO = "kb-nuevo"
   ```

3. **Create search index and Knowledge Base**:
   - Run `scripts/setup_indexes.sh` or create via Azure Portal
   - Run `scripts/setup_foundry_devops.py` to create the KB
   - Seed the index using `scripts/seed_indexes.py` as reference

4. **Register in orchestrator.py**:
   - Add import of the new instructions constant
   - Add a `TrackingSearchProvider` with the new KB name
   - Add the agent to the `specialists` dict
   - Update `ROUTER_INSTRUCTIONS` and `_KEYWORDS` with new routing rules

5. **Export from `__init__.py`** (add to imports and `__all__`)

## Running Agents

Each agent can be run directly for testing:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run individual agents
python -m app.backend.agents.politicas_agent
python -m app.backend.agents.runbooks_agent
python -m app.backend.agents.herramientas_agent

# Run full orchestrated workflow
python -m app.backend.agents.orchestrator
```

## Configuration

Agents use environment variables with defaults (see `config.py`):

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_SEARCH_ENDPOINT` | hardcoded in config.py | Search service endpoint |
| `AZURE_OPENAI_ENDPOINT` | hardcoded in config.py | OpenAI endpoint |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-4o-mini` | Model deployment name |

## Key Concepts

### FoundryIQ Agentic Retrieval (Knowledge Base mode)

The orchestrator uses `knowledge_base_name` to leverage FoundryIQ's agentic retrieval,
which synthesizes answers across multiple knowledge sources:

```python
AzureAISearchContextProvider(
    "politicas-search",
    endpoint=SEARCH_ENDPOINT,
    credential=credential,
    mode="agentic",
    knowledge_base_name=KB_POLITICAS,
    retrieval_reasoning_effort="low",
    knowledge_base_output_mode="answer_synthesis",
)
```

### Semantic Search (individual agent mode)

Individual agents (e.g. `politicas_agent.py`) use `index_name` with semantic search
for direct, lightweight queries without KB overhead:

```python
AzureAISearchContextProvider(
    "politicas-search",
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_POLITICAS,
    credential=credential,
    mode="semantic",
    semantic_configuration_name="default",
)
```

### RBAC Requirements

Run `scripts/setup_rbac.sh` to assign required roles:
- `Cognitive Services User` on OpenAI resource
- `Search Index Data Reader` on Search service
- `Search Service Contributor` on Search service (for KB management)

## Deploying

```bash
azd up  # Full deployment
```
