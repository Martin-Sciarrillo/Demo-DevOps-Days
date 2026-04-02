"""
Crea los índices nuevos (index-politicas, index-runbooks, index-herramientas)
copiando el schema y los documentos desde los viejos (index-hr, index-marketing, index-products).
"""
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from azure.identity import DefaultAzureCredential

SEARCH_ENDPOINT = "https://srch-jnlr3ry4yf2o6.search.windows.net"
API_VERSION = "2024-07-01"

INDEX_MAP = {
    "index-hr":        "index-politicas",
    "index-marketing": "index-runbooks",
    "index-products":  "index-herramientas",
}

SCHEMA = {
    "fields": [
        {"name": "id",           "type": "Edm.String",          "key": True,  "filterable": True},
        {"name": "content",      "type": "Edm.String",          "searchable": True, "analyzer": "standard.lucene"},
        {"name": "title",        "type": "Edm.String",          "searchable": True, "filterable": True, "sortable": True},
        {"name": "category",     "type": "Edm.String",          "searchable": True, "filterable": True, "facetable": True},
        {"name": "lastModified", "type": "Edm.DateTimeOffset",  "filterable": True, "sortable": True},
        {"name": "url",          "type": "Edm.String",          "filterable": True},
    ],
    "semantic": {
        "defaultConfiguration": "default",
        "configurations": [{
            "name": "default",
            "prioritizedFields": {
                "titleField": {"fieldName": "title"},
                "prioritizedContentFields": [{"fieldName": "content"}],
                "prioritizedKeywordsFields": [{"fieldName": "category"}],
            },
        }],
    },
}


def get_token():
    cred = DefaultAzureCredential()
    token = cred.get_token("https://search.azure.com/.default")
    return token.token


def request(method, url, token, body=None):
    data = json.dumps(body).encode("utf-8") if body else None
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, json.loads(raw) if raw else {}


def create_index(name, token):
    schema = {"name": name, **SCHEMA}
    url = f"{SEARCH_ENDPOINT}/indexes/{name}?api-version={API_VERSION}"
    status, body = request("PUT", url, token, schema)
    if status in (200, 201):
        print(f"  ✓ Índice creado: {name}")
    else:
        print(f"  ! {name}: HTTP {status} — {body.get('error', {}).get('message', body)}")


def get_documents(index_name, token):
    url = f"{SEARCH_ENDPOINT}/indexes/{index_name}/docs?api-version={API_VERSION}&$top=100&search=*"
    status, body = request("GET", url, token)
    if status == 200:
        docs = body.get("value", [])
        print(f"  ✓ {len(docs)} documentos obtenidos de '{index_name}'")
        return docs
    else:
        print(f"  ! Error leyendo '{index_name}': HTTP {status}")
        return []


def upload_documents(index_name, docs, token):
    # Strip @odata fields, add @search.action
    clean = []
    for d in docs:
        doc = {k: v for k, v in d.items() if not k.startswith("@")}
        doc["@search.action"] = "mergeOrUpload"
        clean.append(doc)

    url = f"{SEARCH_ENDPOINT}/indexes/{index_name}/docs/index?api-version={API_VERSION}"
    status, body = request("POST", url, token, {"value": clean})
    if status in (200, 207):
        print(f"  ✓ {len(clean)} documentos subidos a '{index_name}'")
    else:
        print(f"  ! Error subiendo a '{index_name}': HTTP {status} — {body}")


def delete_index(name, token):
    url = f"{SEARCH_ENDPOINT}/indexes/{name}?api-version={API_VERSION}"
    headers = {"Authorization": f"Bearer {token}"}
    req = urllib.request.Request(url, headers=headers, method="DELETE")
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"  ✓ Índice eliminado: {name} (HTTP {resp.status})")
    except urllib.error.HTTPError as e:
        print(f"  ! No se pudo eliminar '{name}': HTTP {e.code} — {e.read().decode()}")


def main():
    print("Obteniendo token Azure AD...")
    token = get_token()
    print("Token OK\n")

    print("=== Paso 1: Crear índices nuevos ===")
    for new_name in INDEX_MAP.values():
        create_index(new_name, token)

    print("\n=== Paso 2: Copiar documentos ===")
    for old_name, new_name in INDEX_MAP.items():
        print(f"\n{old_name} → {new_name}")
        docs = get_documents(old_name, token)
        if docs:
            upload_documents(new_name, docs, token)

    print("\n=== Paso 3: Eliminar índices viejos ===")
    for old_name in INDEX_MAP.keys():
        delete_index(old_name, token)

    print("\n¡Listo! Acordate de reiniciar uvicorn.")


if __name__ == "__main__":
    main()
