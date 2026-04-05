"""
Setup FoundryIQ Knowledge Sources y Knowledge Bases para DevOps Days
Usa DefaultAzureCredential (RBAC, sin api-key)
"""

import json
import sys
import time
import requests
from azure.identity import DefaultAzureCredential

SEARCH_ENDPOINT = "https://srch-jnlr3ry4yf2o6.search.windows.net"
OPENAI_ENDPOINT = "https://cog-jnlr3ry4yf2o6.openai.azure.com/"
API_VERSION = "2025-11-01-preview"


def get_token():
    cred = DefaultAzureCredential()
    token = cred.get_token("https://search.azure.com/.default")
    return token.token


def put_resource(token, path, payload):
    url = f"{SEARCH_ENDPOINT}{path}?api-version={API_VERSION}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    r = requests.put(url, headers=headers, json=payload)
    return r.status_code, r.json()


def list_resource(token, path):
    url = f"{SEARCH_ENDPOINT}{path}?api-version={API_VERSION}"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    return r.json().get("value", [])


# ─────────────────────────────────────────────
# Knowledge Sources
# ─────────────────────────────────────────────
KNOWLEDGE_SOURCES = [
    {
        "name": "ks-politicas",
        "kind": "searchIndex",
        "description": "Políticas DevOps: on-call, guardia, SLA/SLO, postmortem, cultura blameless",
        "searchIndexParameters": {"searchIndexName": "index-politicas"},
    },
    {
        "name": "ks-runbooks",
        "kind": "searchIndex",
        "description": "Runbooks operacionales, playbooks de incidentes P1/P2, troubleshooting paso a paso",
        "searchIndexParameters": {"searchIndexName": "index-runbooks"},
    },
    {
        "name": "ks-herramientas",
        "kind": "searchIndex",
        "description": "Catálogo de herramientas internas: Kubernetes, Terraform, Vault, CI/CD, ArgoCD, Grafana",
        "searchIndexParameters": {"searchIndexName": "index-herramientas"},
    },
]

# ─────────────────────────────────────────────
# Knowledge Bases
# ─────────────────────────────────────────────
KNOWLEDGE_BASES = [
    {
        "name": "kb-politicas",
        "description": "Base de conocimiento de Políticas DevOps Days CORP",
        "retrievalInstructions": "Buscar información sobre políticas de on-call, rotaciones de guardia, niveles de severidad de incidentes, SLA/SLO, procesos de postmortem, cultura blameless, compensación de guardia y certificaciones.",
        "answerInstructions": "Respondé en castellano rioplatense. Sé específico y citá las fuentes cuando sea posible.",
        "outputMode": "answerSynthesis",
        "knowledgeSources": [{"name": "ks-politicas"}],
        "models": [{
            "kind": "azureOpenAI",
            "azureOpenAIParameters": {
                "resourceUri": OPENAI_ENDPOINT,
                "deploymentId": "gpt-4o",
                "modelName": "gpt-4o",
            },
        }],
        "retrievalReasoningEffort": {"kind": "medium"},
    },
    {
        "name": "kb-runbooks",
        "description": "Base de conocimiento de Runbooks DevOps Days CORP",
        "retrievalInstructions": "Buscar runbooks operacionales, playbooks de incidentes, procedimientos de respuesta a alertas y pasos de troubleshooting.",
        "answerInstructions": "Respondé en castellano rioplatense. Listá los pasos con claridad y citá las fuentes.",
        "outputMode": "answerSynthesis",
        "knowledgeSources": [{"name": "ks-runbooks"}],
        "models": [{
            "kind": "azureOpenAI",
            "azureOpenAIParameters": {
                "resourceUri": OPENAI_ENDPOINT,
                "deploymentId": "gpt-4o",
                "modelName": "gpt-4o",
            },
        }],
        "retrievalReasoningEffort": {"kind": "medium"},
    },
    {
        "name": "kb-herramientas",
        "description": "Base de conocimiento de Herramientas DevOps Days CORP",
        "retrievalInstructions": "Buscar información sobre herramientas internas de infraestructura, CI/CD, monitoring, observabilidad y gestión de secretos.",
        "answerInstructions": "Respondé en castellano rioplatense. Incluí casos de uso y cómo acceder a cada herramienta.",
        "outputMode": "answerSynthesis",
        "knowledgeSources": [{"name": "ks-herramientas"}],
        "models": [{
            "kind": "azureOpenAI",
            "azureOpenAIParameters": {
                "resourceUri": OPENAI_ENDPOINT,
                "deploymentId": "gpt-4o",
                "modelName": "gpt-4o",
            },
        }],
        "retrievalReasoningEffort": {"kind": "medium"},
    },
]


def main():
    print("\n🔐 Obteniendo token Azure...\n")
    token = get_token()

    # ── Knowledge Sources ──
    print("═" * 55)
    print("  Creando Knowledge Sources")
    print("═" * 55)
    for ks in KNOWLEDGE_SOURCES:
        code, resp = put_resource(token, f"/knowledgesources/{ks['name']}", ks)
        status = "✅" if code in (200, 201) else f"⚠️  HTTP {code}"
        print(f"  {status}  {ks['name']}  →  {ks['searchIndexParameters']['searchIndexName']}")
        if code not in (200, 201):
            print(f"       {resp}")
        time.sleep(0.5)

    print()

    # ── Knowledge Bases ──
    print("═" * 55)
    print("  Creando Knowledge Bases")
    print("═" * 55)
    for kb in KNOWLEDGE_BASES:
        code, resp = put_resource(token, f"/knowledgebases/{kb['name']}", kb)
        status = "✅" if code in (200, 201) else f"⚠️  HTTP {code}"
        ks_names = [k["name"] for k in kb["knowledgeSources"]]
        print(f"  {status}  {kb['name']}  →  {ks_names}")
        if code not in (200, 201):
            print(f"       {resp}")
        time.sleep(0.5)

    print()

    # ── Verificación ──
    print("═" * 55)
    print("  Verificando estado final")
    print("═" * 55)
    kss = list_resource(token, "/knowledgesources")
    kbs = list_resource(token, "/knowledgebases")
    print(f"  Knowledge Sources: {[k['name'] for k in kss]}")
    print(f"  Knowledge Bases:   {[k['name'] for k in kbs]}")
    print()

    if len(kss) == 3 and len(kbs) == 3:
        print("🎉 Todo listo. Ahora actualizá el backend a mode='agentic'.\n")
        return 0
    else:
        print("⚠️  Algo no se creó bien. Revisá los errores arriba.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
