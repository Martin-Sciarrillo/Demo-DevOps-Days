# Demo DevOps Days — Multi-Agent Orchestration con Azure AI

> Demo presentada en **DevOps Days** por [Martin Sciarrillo](https://github.com/Martin-Sciarrillo)

Demo de orquestación multi-agente usando el **Microsoft Agent Framework SDK** y **Azure AI Search** con búsqueda semántica. Simula un asistente interno de DevOps Days CORP que un ingeniero de guardia puede consultar a las 2am para resolver incidentes.

## Qué hace la demo

Un **agente orquestador** recibe la pregunta del usuario, decide a qué especialista enviarla y devuelve una respuesta fundamentada en la base de conocimiento correspondiente:

```
Pregunta del usuario
        │
        ▼
┌───────────────────┐
│    ORQUESTADOR    │  analiza el intent y enruta
└──────┬────────────┘
       │
   ┌───┴──────────────────────┐
   │                          │
   ▼                          ▼                          ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Agente Políticas │  │ Agente Runbooks  │  │ Agente Herram.   │
│ Soporte & On-Call│  │ Ops SRE          │  │ Plataforma       │
│                  │  │                  │  │                  │
│ index-hr         │  │ index-marketing  │  │ index-products   │
│ · On-call/guardia│  │ · Runbooks       │  │ · Kubernetes/EKS │
│ · SLA/SLO        │  │ · Playbooks P1   │  │ · Terraform      │
│ · Postmortem     │  │ · Troubleshooting│  │ · Vault/Grafana  │
│ · Certificaciones│  │ · Alertas        │  │ · CI/CD/ArgoCD   │
└──────────────────┘  └──────────────────┘  └──────────────────┘
        │                      │                      │
        └──────────────────────┴──────────────────────┘
                               │
                    Azure AI Search (semántico)
```

## Stack técnico

| Capa | Tecnología |
|------|-----------|
| Agentes | Microsoft Agent Framework SDK (`agent-framework`, `agent-framework-openai`) |
| LLM | Azure OpenAI `gpt-4o` vía `OpenAIChatCompletionClient` |
| Retrieval | Azure AI Search — modo semántico (`AzureAISearchContextProvider`) |
| Auth | `DefaultAzureCredential` — sin API keys, solo RBAC |
| Backend | FastAPI + uvicorn |
| Frontend | React (build estático servido por FastAPI) |

## Bases de conocimiento

| Índice | Agente | Contenido |
|--------|--------|-----------|
| `index-hr` | Políticas / Soporte & On-Call | Políticas de guardia, rotaciones, niveles de severidad, SLA/SLO, postmortem blameless, compensación, certificaciones |
| `index-marketing` | Runbooks / Operaciones SRE | Runbooks operacionales: CPU alto, CrashLoopBackOff, rollback, DB lenta, latencia, disco, SSL, playbook P1 |
| `index-products` | Herramientas / Plataforma | Catálogo de herramientas: Kubernetes/EKS, Terraform, Vault, Grafana+Prometheus, GitHub Actions, ArgoCD, Datadog, PagerDuty |

## Requisitos previos

- Suscripción Azure con rol **Owner** o **Contributor + User Access Administrator**
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
- [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- Python 3.11+

## Setup

### 1. Clonar y crear entorno

```bash
git clone https://github.com/Martin-Sciarrillo/Demo-DevOps-Days.git
cd Demo-DevOps-Days

python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# Linux/Mac
source .venv/bin/activate

pip install -r requirements-dev.txt
```

### 2. Desplegar infraestructura

```bash
az login && azd auth login
azd up
```

### 3. Crear índices y cargar datos

```bash
./scripts/setup_indexes.sh
./scripts/upload_sample_data.sh
```

### 4. Configurar RBAC en Azure Search (manual)

En Azure Portal: **Search service → Keys → "Both"** (API keys + RBAC).

### 5. Configurar variables de entorno

Crear un archivo `.env` en la raíz del repo:

```env
AZURE_OPENAI_ENDPOINT=https://<tu-recurso>.openai.azure.com/
AZURE_SEARCH_ENDPOINT=https://<tu-recurso>.search.windows.net
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

### 6. Correr la app

```bash
cd app/backend
uvicorn main:app --reload
```

Abrir [http://localhost:8000](http://localhost:8000).

Al arrancar, uvicorn inicializa la conexión con Azure AD, el cliente OpenAI y los tres proveedores de búsqueda una sola vez — sin overhead por request.

## Probar desde línea de comandos

```bash
# Activar venv primero
.venv\Scripts\Activate.ps1

python app/backend/agents/orchestrator.py
```

Consultas de ejemplo:
- `"¿Cuál es el procedimiento de escalado para un incidente P1?"`
- `"¿Cómo resuelvo un CrashLoopBackOff en producción?"`
- `"¿Qué herramienta usamos para gestión de secretos?"`

## Estructura del proyecto

```
├── app/
│   └── backend/
│       ├── main.py                  # FastAPI app + lifespan (warmup de agentes)
│       ├── agents/
│       │   ├── orchestrator.py      # Router + agentes especialistas + OrchestratorState
│       │   ├── config.py            # Endpoints y nombres de índices
│       │   ├── hr_agent.py          # Agente standalone de políticas
│       │   ├── marketing_agent.py   # Agente standalone de runbooks
│       │   └── products_agent.py    # Agente standalone de herramientas
│       └── static/                  # Frontend React (build pre-compilado)
├── infra/                           # Bicep IaC
├── scripts/                         # Scripts de setup y despliegue
│   ├── setup_indexes.sh
│   ├── upload_sample_data.sh
│   ├── setup_rbac.sh
│   └── auth_init.sh / auth_init.ps1
└── docs/
```

## Troubleshooting

| Error | Solución |
|-------|----------|
| `403 Forbidden` en Search | Portal → Search → Keys → **"Both"** |
| `ModuleNotFoundError: config` | Correr uvicorn desde `app/backend/`, no desde la raíz |
| `ModuleNotFoundError: dotenv` | Activar el venv: `.venv\Scripts\Activate.ps1` |
| Respuestas genéricas sin datos | Verificar que los índices tengan documentos (`setup_indexes.sh` + `upload_sample_data.sh`) |
| Demora en primer request | Normal: es el warmup del token AAD. Desde el segundo request es más rápido. |

## Licencia

MIT
