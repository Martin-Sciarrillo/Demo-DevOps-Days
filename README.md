# FoundryIQ and Agent Framework Demo

> Demo presentada en **DevOps Days** por [Martin Sciarrillo](https://github.com/Martin-Sciarrillo)

A multi-agent orchestration demo using Microsoft Agent Framework SDK and Azure AI Foundry with Azure AI Search for grounded retrieval. Simula un asistente interno que un ingeniero de guardia puede consultar para resolver incidentes.

![Demo Screenshot](docs/demo-screenshot.png)

## Features

- **Multi-Agent Orchestration**: Intelligent routing of queries to specialized agents (Políticas, Runbooks, Herramientas)
- **Microsoft Agent Framework SDK**: Built on the official `agent-framework` Python SDK
- **Azure AI Search**: Semantic retrieval mode with `gpt-4o` for grounded responses
- **RBAC-Only Authentication**: No API keys - uses DefaultAzureCredential for all services
- **Fully Automated Deployment**: Infrastructure as Code with Bicep + setup scripts

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              User Query                                       │
│            "¿Cómo resuelvo un CrashLoopBackOff en producción?"               │
└─────────────────────────────────┬────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR AGENT                                    │
│                                                                               │
│   • Analyzes user intent                                                      │
│   • Routes to appropriate specialist agent                                    │
│   • Returns grounded response with citations                                  │
└───────────┬─────────────────────┬─────────────────────┬──────────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│  AGENTE POLÍTICAS │  │  AGENTE RUNBOOKS  │  │ AGENTE HERRAM.    │
│  Soporte & On-Call│  │  Operaciones SRE  │  │ Plataforma        │
│                   │  │                   │  │                   │
│ index-hr          │  │ index-marketing   │  │ index-products    │
│ • On-call/guardia │  │ • Runbooks ops    │  │ • Kubernetes/EKS  │
│ • SLA/SLO         │  │ • Playbooks P1    │  │ • Terraform/Vault │
│ • Postmortem      │  │ • Troubleshooting │  │ • CI/CD/ArgoCD    │
└─────────┬─────────┘  └─────────┬─────────┘  └─────────┬─────────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           AZURE AI SEARCH                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                    ÍNDICES (búsqueda semántica)                         │  │
│  │                                                                         │  │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │  │
│  │  │   index-hr   │    │index-marketing│    │index-products│              │  │
│  │  │   gpt-4o     │    │   gpt-4o     │    │   gpt-4o     │              │  │
│  │  └──────────────┘    └──────────────┘    └──────────────┘              │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Azure subscription with Owner or Contributor + User Access Administrator
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
- [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- [Python 3.11+](https://www.python.org/downloads/)

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/Martin-Sciarrillo/Demo-DevOps-Days.git
cd Demo-DevOps-Days

# Create virtual environment
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1
# Linux/Mac
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt
```

### 2. Deploy Infrastructure

```bash
az login && azd auth login
azd up
```

### 3. Setup Search Indexes

```bash
./scripts/setup_indexes.sh
./scripts/upload_sample_data.sh
```

### 4. Configure Search RBAC (Manual)

In Azure Portal: Search service → Keys → Set to **"Both"** (API keys + RBAC)

### 5. Configure Environment

Create a `.env` file at the repo root:

```env
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_SEARCH_ENDPOINT=https://<your-resource>.search.windows.net
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

### 6. Run the App

```bash
cd app/backend
uvicorn main:app --reload
```

Open [http://localhost:8000](http://localhost:8000)

### 7. Test the Orchestrator

```bash
python app/backend/agents/orchestrator.py
```

Try: `"¿Cuál es el procedimiento de escalado para un P1?"` or `"¿Qué herramienta usamos para gestión de secretos?"`

## Project Structure

```
├── app/backend/
│   ├── main.py              # FastAPI app (initializes agents once at startup)
│   └── agents/
│       ├── orchestrator.py  # Router + specialist agents + OrchestratorState singleton
│       ├── config.py        # Endpoints and index names
│       ├── hr_agent.py      # Standalone políticas agent
│       ├── marketing_agent.py # Standalone runbooks agent
│       └── products_agent.py  # Standalone herramientas agent
├── infra/                   # Bicep IaC templates
├── scripts/                 # Setup and deployment scripts
└── docs/                    # Documentation
```

## Knowledge Base Mapping

| Agent | Index | Content |
|-------|-------|---------|
| Políticas (Soporte & On-Call) | index-hr | On-call policies, rotaciones, SLA/SLO, postmortem, certificaciones |
| Runbooks (Operaciones SRE) | index-marketing | Runbooks operacionales, playbooks P1, troubleshooting paso a paso |
| Herramientas (Plataforma) | index-products | Kubernetes/EKS, Terraform, Vault, Grafana, GitHub Actions, ArgoCD, Datadog, PagerDuty |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| 403 Forbidden | Portal → Search → Keys → "Both" |
| `ModuleNotFoundError: config` | Run uvicorn from `app/backend/`, not repo root |
| `ModuleNotFoundError: dotenv` | Activate venv first: `.venv\Scripts\Activate.ps1` |
| Generic responses | Ensure indexes have documents (`upload_sample_data.sh`) |
| Slow first response | Normal — Azure AD token warmup. Subsequent requests are faster. |

## License

MIT License
