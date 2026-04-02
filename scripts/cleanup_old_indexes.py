"""
Elimina las knowledge sources que referencian los índices viejos
y luego elimina los índices viejos (index-hr, index-marketing, index-products).

Orden obligatorio:
  1. Borrar knowledge sources
  2. Borrar índices
"""
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from azure.identity import DefaultAzureCredential

SEARCH_ENDPOINT = "https://srch-jnlr3ry4yf2o6.search.windows.net"
KB_API_VERSION  = "2025-11-01-preview"
KS_API_VERSION  = "2025-11-01-preview"
IDX_API_VERSION = "2024-07-01"

# Knowledge sources que bloquean el borrado de los índices viejos
KNOWLEDGE_BASES = [
    "kb1-hr",
    "kb2-marketing",
    "kb3-products",
]

KNOWLEDGE_SOURCES = [
    "ks-hr-aisearch",
    "ks-hr-sharepoint",
    "ks-marketing",
    "ks-products",
]

OLD_INDEXES = [
    "index-hr",
    "index-marketing",
    "index-products",
]


def get_token():
    return DefaultAzureCredential().get_token("https://search.azure.com/.default").token


def delete(url, token):
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def main():
    print("Obteniendo token Azure AD...")
    token = get_token()
    print("Token OK\n")

    print("=== Paso 1: Eliminar Knowledge Bases ===")
    for kb in KNOWLEDGE_BASES:
        url = f"{SEARCH_ENDPOINT}/knowledgebases/{kb}?api-version={KB_API_VERSION}"
        status, msg = delete(url, token)
        if status == 204:
            print(f"  ✓ Eliminada: {kb}")
        elif status == 404:
            print(f"  - No existe: {kb}")
        else:
            print(f"  ! Error {kb}: HTTP {status} — {msg[:200]}")

    print("\n=== Paso 2: Eliminar Knowledge Sources ===")
    for ks in KNOWLEDGE_SOURCES:
        url = f"{SEARCH_ENDPOINT}/knowledgesources/{ks}?api-version={KS_API_VERSION}"
        status, msg = delete(url, token)
        if status == 204:
            print(f"  ✓ Eliminada: {ks}")
        elif status == 404:
            print(f"  - No existe (ya fue eliminada): {ks}")
        else:
            print(f"  ! Error {ks}: HTTP {status} — {msg[:200]}")

    print("\n=== Paso 3: Eliminar Índices Viejos ===")
    for idx in OLD_INDEXES:
        url = f"{SEARCH_ENDPOINT}/indexes/{idx}?api-version={IDX_API_VERSION}"
        status, msg = delete(url, token)
        if status == 204:
            print(f"  ✓ Eliminado: {idx}")
        elif status == 404:
            print(f"  - No existe (ya fue eliminado): {idx}")
        else:
            print(f"  ! Error {idx}: HTTP {status} — {msg[:200]}")

    print("\n¡Listo!")


if __name__ == "__main__":
    main()
