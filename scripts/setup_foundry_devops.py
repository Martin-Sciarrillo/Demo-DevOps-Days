"""
Setup FoundryIQ Knowledge Sources y Knowledge Bases para DevOps Days
Usa DefaultAzureCredential (RBAC, sin api-key)

Fuentes:
  searchIndex  — índices propios en Azure AI Search
  web (remote) — docs públicos multi-vendor: AWS, Terraform, Ansible/PagerDuty
"""

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


SUCCESS_CODES = (200, 201, 204)

def put_resource(token, path, payload):
    url = f"{SEARCH_ENDPOINT}{path}?api-version={API_VERSION}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.put(url, headers=headers, json=payload)
    try:
        return r.status_code, r.json()
    except Exception:
        # 204 No Content = success (update sin body)
        return r.status_code, {}


def patch_resource(token, path, payload):
    """PATCH para actualizar un recurso existente (ej: agregar KSs a un KB)."""
    url = f"{SEARCH_ENDPOINT}{path}?api-version={API_VERSION}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/merge-patch+json",
    }
    r = requests.patch(url, headers=headers, json=payload)
    return r.status_code, r.json()


def list_resource(token, path):
    url = f"{SEARCH_ENDPOINT}{path}?api-version={API_VERSION}"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    return r.json().get("value", [])


def web_ks(name, description, domains):
    """Helper para crear una web Knowledge Source con el schema correcto."""
    return {
        "name": name,
        "kind": "web",
        "description": description,
        "webParameters": {
            "domains": {
                "allowedDomains": [
                    {"address": d, "includeSubpages": True} for d in domains
                ]
            }
        },
    }


# ─────────────────────────────────────────────
# Knowledge Sources — searchIndex (propios)
# ─────────────────────────────────────────────
KS_INDEX = [
    {
        "name": "ks-politicas",
        "kind": "searchIndex",
        "description": "Políticas DevOps internas: on-call, guardia, SLA/SLO, postmortem, cultura blameless",
        "searchIndexParameters": {"searchIndexName": "index-politicas"},
    },
    {
        "name": "ks-runbooks",
        "kind": "searchIndex",
        "description": "Runbooks operacionales internos, playbooks de incidentes P1/P2, troubleshooting",
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
# Knowledge Sources — web (multi-vendor, públicos)
# ─────────────────────────────────────────────
KS_WEB = [
    # kb-politicas: políticas y cultura SRE — AWS Well-Architected + PagerDuty
    web_ks(
        "ks-web-aws-reliability",
        "AWS Well-Architected Reliability Pillar: incident response, escalation, SLA/SLO patterns",
        [
            "https://docs.aws.amazon.com/wellarchitected",
            "https://aws.amazon.com/blogs/mt",          # Management & Governance
        ],
    ),
    web_ks(
        "ks-web-pagerduty",
        "PagerDuty docs: on-call schedules, escalation policies, incident response best practices",
        ["https://support.pagerduty.com"],
    ),
    # kb-runbooks: procedimientos operacionales — Terraform registry
    web_ks(
        "ks-web-terraform",
        "Terraform documentation: providers, modules, IaC best practices y ejemplos de infraestructura",
        [
            "https://developer.hashicorp.com/terraform",
            "https://registry.terraform.io",
        ],
    ),
    web_ks(
        "ks-web-aws-ops",
        "AWS operational runbooks: EKS, EC2, RDS troubleshooting procedures y incident playbooks",
        [
            "https://docs.aws.amazon.com/eks",
            "https://docs.aws.amazon.com/systems-manager",
        ],
    ),
    # kb-herramientas: catálogo multi-vendor — Ansible + HashiCorp
    web_ks(
        "ks-web-ansible",
        "Ansible documentation y Galaxy: automatización, playbooks, roles para infraestructura multi-cloud",
        [
            "https://docs.ansible.com",
            "https://galaxy.ansible.com",
        ],
    ),
    web_ks(
        "ks-web-hashicorp",
        "HashiCorp tools: Vault secrets management, Consul service mesh, Nomad workload orchestration",
        [
            "https://developer.hashicorp.com/vault",
            "https://developer.hashicorp.com/consul",
        ],
    ),
]

# ─────────────────────────────────────────────
# Knowledge Bases — con todas las fuentes
# ─────────────────────────────────────────────
KNOWLEDGE_BASES = [
    {
        "name": "kb-politicas",
        "description": "Base de conocimiento de Políticas DevOps Days CORP",
        "retrievalInstructions": (
            "Buscar información sobre políticas de on-call, rotaciones de guardia, niveles de severidad, "
            "SLA/SLO, procesos de postmortem, cultura blameless, compensación de guardia y certificaciones. "
            "Incluir mejores prácticas de la industria (AWS Well-Architected, PagerDuty)."
        ),
        "answerInstructions": "Respondé en castellano rioplatense. Sé específico y citá las fuentes.",
        "outputMode": "answerSynthesis",
        "knowledgeSources": [
            {"name": "ks-politicas"},
            {"name": "ks-web-aws-reliability"},
            {"name": "ks-web-pagerduty"},
        ],
        "models": [{"kind": "azureOpenAI", "azureOpenAIParameters": {
            "resourceUri": OPENAI_ENDPOINT, "deploymentId": "gpt-4o", "modelName": "gpt-4o",
        }}],
        "retrievalReasoningEffort": {"kind": "medium"},
    },
    {
        "name": "kb-runbooks",
        "description": "Base de conocimiento de Runbooks DevOps Days CORP",
        "retrievalInstructions": (
            "Buscar runbooks operacionales, playbooks de incidentes, procedimientos de troubleshooting. "
            "Incluir procedimientos de Terraform para IaC y runbooks operacionales de AWS."
        ),
        "answerInstructions": "Respondé en castellano rioplatense. Listá los pasos con claridad y citá las fuentes.",
        "outputMode": "answerSynthesis",
        "knowledgeSources": [
            {"name": "ks-runbooks"},
            {"name": "ks-web-terraform"},
            {"name": "ks-web-aws-ops"},
        ],
        "models": [{"kind": "azureOpenAI", "azureOpenAIParameters": {
            "resourceUri": OPENAI_ENDPOINT, "deploymentId": "gpt-4o", "modelName": "gpt-4o",
        }}],
        "retrievalReasoningEffort": {"kind": "medium"},
    },
    {
        "name": "kb-herramientas",
        "description": "Base de conocimiento de Herramientas DevOps Days CORP",
        "retrievalInstructions": (
            "Buscar información sobre herramientas de infraestructura, CI/CD, monitoring, observabilidad "
            "y gestión de secretos. Incluir Ansible para automatización y HashiCorp para secrets/service mesh."
        ),
        "answerInstructions": "Respondé en castellano rioplatense. Incluí casos de uso y cómo acceder a cada herramienta.",
        "outputMode": "answerSynthesis",
        "knowledgeSources": [
            {"name": "ks-herramientas"},
            {"name": "ks-web-ansible"},
            {"name": "ks-web-hashicorp"},
        ],
        "models": [{"kind": "azureOpenAI", "azureOpenAIParameters": {
            "resourceUri": OPENAI_ENDPOINT, "deploymentId": "gpt-4o", "modelName": "gpt-4o",
        }}],
        "retrievalReasoningEffort": {"kind": "medium"},
    },
]


def main():
    print("\n Obteniendo token Azure...\n")
    token = get_token()

    # ── Knowledge Sources: searchIndex ──
    print("=" * 60)
    print("  Knowledge Sources — searchIndex (propios)")
    print("=" * 60)
    for ks in KS_INDEX:
        code, resp = put_resource(token, f"/knowledgesources/{ks['name']}", ks)
        status = "OK" if code in SUCCESS_CODES else f"ERROR HTTP {code}"
        print(f"  [{status}]  {ks['name']}  ->  {ks['searchIndexParameters']['searchIndexName']}")
        if code not in (200, 201):
            print(f"         {resp.get('error', {}).get('message', resp)}")
        time.sleep(0.3)

    print()

    # ── Knowledge Sources: web (multi-vendor) ──
    print("=" * 60)
    print("  Knowledge Sources — web (multi-vendor)")
    print("=" * 60)
    for ks in KS_WEB:
        code, resp = put_resource(token, f"/knowledgesources/{ks['name']}", ks)
        status = "OK" if code in SUCCESS_CODES else f"ERROR HTTP {code}"
        domains = [d["address"] for d in ks["webParameters"]["domains"]["allowedDomains"]]
        print(f"  [{status}]  {ks['name']}")
        print(f"           {domains}")
        if code not in (200, 201):
            print(f"         {resp.get('error', {}).get('message', resp)}")
        time.sleep(0.3)

    print()

    # ── Knowledge Bases ──
    print("=" * 60)
    print("  Knowledge Bases (con fuentes multi-vendor)")
    print("=" * 60)
    for kb in KNOWLEDGE_BASES:
        code, resp = put_resource(token, f"/knowledgebases/{kb['name']}", kb)
        status = "OK" if code in SUCCESS_CODES else f"ERROR HTTP {code}"
        ks_names = [k["name"] for k in kb["knowledgeSources"]]
        print(f"  [{status}]  {kb['name']}")
        print(f"           Sources: {ks_names}")
        if code not in (200, 201):
            print(f"         {resp.get('error', {}).get('message', resp)}")
        time.sleep(0.5)

    print()

    # ── Verificación final ──
    print("=" * 60)
    print("  Estado final")
    print("=" * 60)
    kss = list_resource(token, "/knowledgesources")
    kbs = list_resource(token, "/knowledgebases")
    print(f"  Knowledge Sources ({len(kss)}): {[k['name'] for k in kss]}")
    print(f"  Knowledge Bases   ({len(kbs)}): {[k['name'] for k in kbs]}")
    print()

    expected_ks = len(KS_INDEX) + len(KS_WEB)
    if len(kss) >= expected_ks and len(kbs) == 3:
        print("  Todo listo. KBs multi-vendor activas en Foundry IQ.\n")
        return 0
    else:
        print("  Algo no se creo bien. Revisa los errores arriba.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
