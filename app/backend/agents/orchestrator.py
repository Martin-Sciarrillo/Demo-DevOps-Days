import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv(Path(__file__).resolve().parents[3] / ".env")
from azure.identity.aio import DefaultAzureCredential

from agent_framework import Agent, Message, Content
from agent_framework_openai import OpenAIChatCompletionClient
from agent_framework.azure import AzureAISearchContextProvider


class TrackingSearchProvider(AzureAISearchContextProvider):
    """Wraps AzureAISearchContextProvider to capture Foundry IQ source references per query."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_references: list = []

    async def _agentic_search(self, messages):
        result_messages = await super()._agentic_search(messages)
        refs = []
        for msg in result_messages:
            if msg.contents:
                for content in msg.contents:
                    if hasattr(content, "annotations") and content.annotations:
                        refs.extend(content.annotations)
        self.last_references = refs
        return result_messages

from config import OPENAI_ENDPOINT, SEARCH_ENDPOINT, MODEL, KB_POLITICAS, KB_RUNBOOKS, KB_HERRAMIENTAS

POLITICAS_INSTRUCTIONS = """Sos el Agente de Políticas DevOps de DevOps Days CORP.
Respondé preguntas sobre políticas de on-call, rotaciones de guardia, niveles de severidad de incidentes, SLAs/SLOs,
proceso de postmortem, cultura blameless, compensación de guardia y certificaciones usando la base de conocimiento.
Respondé siempre en castellano rioplatense. Sé específico y citá las fuentes cuando sea posible."""

RUNBOOKS_INSTRUCTIONS = """Sos el Agente de Runbooks de DevOps Days CORP.
Respondé preguntas sobre runbooks operacionales, playbooks de incidentes, procedimientos de respuesta a alertas
y pasos de troubleshooting usando la base de conocimiento.
Respondé siempre en castellano rioplatense. Sé específico, listá los pasos y citá las fuentes."""

HERRAMIENTAS_INSTRUCTIONS = """Sos el Agente de Herramientas de DevOps Days CORP.
Respondé preguntas sobre el catálogo de herramientas internas: plataformas de infraestructura, CI/CD, monitoring,
observabilidad, seguridad y gestión de secretos usando la base de conocimiento.
Respondé siempre en castellano rioplatense. Sé específico e incluí casos de uso y cómo acceder a cada herramienta."""

ROUTER_INSTRUCTIONS = """Sos un agente de enrutamiento para un equipo de DevOps/SRE. Analizá la consulta y determiná qué especialista debe manejarla.

- "politicas": políticas de on-call, guardia, escalado, SLA, SLO, postmortem, cultura, compensación, certificaciones
- "herramientas": herramientas internas, plataformas, Kubernetes, Terraform, CI/CD, monitoring, observabilidad, secretos
- "runbooks": runbooks, playbooks, procedimientos operacionales, cómo resolver alertas, troubleshooting paso a paso

Respondé ÚNICAMENTE con uno de estos nombres: politicas, herramientas, runbooks
Solo respondé con el nombre del agente, nada más."""


def user_message(text: str) -> Message:
    return Message(role="user", contents=[Content.from_text(text)])


_KEYWORDS = {
    "politicas": {
        "on-call", "oncall", "guardia", "escalado", "escalamiento", "pagerduty",
        "sla", "slo", "postmortem", "post-mortem", "blameless", "incidente",
        "severidad", "certificacion", "certificación", "compensacion", "compensación",
        "rotacion", "rotación", "política", "politica", "política",
    },
    "runbooks": {
        "runbook", "playbook", "procedimiento", "paso a paso", "troubleshoot",
        "crashloopbackoff", "cpu alto", "rollback", "latencia", "disco lleno",
        "ssl", "alerta", "resolver", "como hago", "cómo hago", "como resuelvo",
        "cómo resuelvo", "pasos para",
    },
    "herramientas": {
        "kubernetes", "k8s", "terraform", "vault", "grafana", "prometheus",
        "github actions", "argocd", "argo", "datadog", "herramienta", "plataforma",
        "ci/cd", "cicd", "monitoreo", "observabilidad", "secreto", "secret",
        "infraestructura", "deploy", "deployment", "helm", "eks", "docker",
    },
}


def keyword_route(query: str) -> str | None:
    q = query.lower()
    scores = {category: sum(1 for kw in kws if kw in q) for category, kws in _KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


async def route_query(router: Agent, query: str) -> str:
    # Intenta clasificar por keywords (cero latencia)
    fast = keyword_route(query)
    if fast:
        return fast
    # Fallback al LLM solo si no hay keywords claras
    resp = await router.run(user_message(query))
    route = (resp.text or "").strip().lower()
    if "politica" in route or "guardia" in route or "sla" in route:
        return "politicas"
    if "runbook" in route or "playbook" in route or "procedimiento" in route:
        return "runbooks"
    if "herramienta" in route or "tool" in route or "plataforma" in route:
        return "herramientas"
    return "politicas"


class OrchestratorState:
    """Singleton state: credential, client, agents — initialized once at startup."""

    def __init__(self):
        self._credential = None
        self._client = None
        self._hr_search = None
        self._marketing_search = None
        self._products_search = None
        self.router = None
        self.specialists = None

    async def start(self):
        self._credential = DefaultAzureCredential()
        self._client = OpenAIChatCompletionClient(
            model=MODEL,
            azure_endpoint=OPENAI_ENDPOINT,
            credential=self._credential,
            api_version="2024-12-01-preview",
        )
        self._hr_search = TrackingSearchProvider(
            "hr-search", endpoint=SEARCH_ENDPOINT,
            credential=self._credential, mode="agentic",
            knowledge_base_name=KB_POLITICAS, retrieval_reasoning_effort="low",
            knowledge_base_output_mode="answer_synthesis",
        )
        self._marketing_search = TrackingSearchProvider(
            "marketing-search", endpoint=SEARCH_ENDPOINT,
            credential=self._credential, mode="agentic",
            knowledge_base_name=KB_RUNBOOKS, retrieval_reasoning_effort="low",
            knowledge_base_output_mode="answer_synthesis",
        )
        self._products_search = TrackingSearchProvider(
            "products-search", endpoint=SEARCH_ENDPOINT,
            credential=self._credential, mode="agentic",
            knowledge_base_name=KB_HERRAMIENTAS, retrieval_reasoning_effort="low",
            knowledge_base_output_mode="answer_synthesis",
        )
        self.router = Agent(client=self._client, instructions=ROUTER_INSTRUCTIONS)
        self.specialists = {
            "politicas": Agent(client=self._client, context_providers=[self._hr_search], instructions=POLITICAS_INSTRUCTIONS),
            "runbooks": Agent(client=self._client, context_providers=[self._marketing_search], instructions=RUNBOOKS_INSTRUCTIONS),
            "herramientas": Agent(client=self._client, context_providers=[self._products_search], instructions=HERRAMIENTAS_INSTRUCTIONS),
        }

    async def stop(self):
        if self._credential:
            await self._credential.close()


_state: OrchestratorState | None = None


async def get_state() -> OrchestratorState:
    global _state
    if _state is None:
        _state = OrchestratorState()
        await _state.start()
    return _state


async def startup():
    await get_state()


async def shutdown():
    global _state
    if _state:
        await _state.stop()
        _state = None


_DOC_TITLES: dict[str, str] = {
    "pol-001": "Proceso de Postmortem Blameless",
    "pol-002": "Política de On-Call y Rotaciones de Guardia",
    "pol-003": "Niveles de Severidad (SEV-1 a SEV-4)",
    "pol-004": "Política de SLA, SLO y Error Budget",
    "pol-005": "Política de Escalación de Incidentes",
    "run-001": "Runbook: CrashLoopBackOff en EKS",
    "run-002": "Runbook: Alto CPU/Memoria en Nodos",
    "run-003": "Runbook: Connection Pool Exhausted (RDS)",
    "run-004": "Runbook: Certificado SSL Expirado",
    "run-005": "Runbook: Rollback de Deploy en Producción",
    "her-001": "Vault — Gestión de Secretos",
    "her-002": "Kubernetes/EKS — Plataforma de Contenedores",
    "her-003": "Terraform — Infraestructura como Código",
    "her-004": "ArgoCD — GitOps y Deploy Continuo",
    "her-005": "Datadog y Grafana — Observabilidad",
}


def _extract_title_from_source_data(source_data) -> str:
    """Try every known shape of source_data to find a human-readable title."""
    if not source_data:
        return ""
    import json as _json
    if isinstance(source_data, str):
        try:
            source_data = _json.loads(source_data)
        except Exception:
            return source_data[:80]
    if isinstance(source_data, dict):
        for key in ("title", "Title", "name", "Name", "chunk_id", "doc_key", "id"):
            val = source_data.get(key)
            if val and not str(val).isdigit():
                return str(val)
    return ""


def _serialize_annotation(ann) -> dict:
    props = ann.get("additional_properties", {}) if hasattr(ann, "get") else {}
    if not isinstance(props, dict):
        props = {}

    # --- title ---
    title = ann.get("title", "") if hasattr(ann, "get") else getattr(ann, "title", "")
    # Foundry IQ returns sequential integers ("0","1","4") as title for internal refs — discard them
    if not title or str(title).isdigit():
        title = _extract_title_from_source_data(props.get("source_data"))
    doc_key = props.get("doc_key", "")
    if not title or str(title).isdigit():
        # Buscar en mapa de títulos conocidos por doc_key
        if doc_key and doc_key in _DOC_TITLES:
            title = _DOC_TITLES[doc_key]
        elif doc_key and not str(doc_key).isdigit():
            title = doc_key
        else:
            title = "Documento interno"

    # --- url --- solo usar si es HTTP real; nunca asignar el activity_source numérico
    raw_url = ann.get("url", "") if hasattr(ann, "get") else getattr(ann, "url", "")
    url = raw_url if isinstance(raw_url, str) and raw_url.startswith("http") else ""
    if not url:
        sd = props.get("source_data")
        if isinstance(sd, dict):
            sd_url = sd.get("url", "") or ""
            if isinstance(sd_url, str) and sd_url.startswith("http"):
                url = sd_url

    # --- debug log (remove after confirming titles are correct) ---
    logger.debug("annotation title=%r url=%r source_data=%r doc_key=%r",
                 title, url, props.get("source_data"), props.get("doc_key"))

    return {
        "title": title,
        "url": url,
        "score": props.get("reranker_score"),
        "activity_source": str(props.get("activity_source", "")),
        "reference_type": props.get("reference_type", ""),
        "doc_key": props.get("doc_key", ""),
    }


async def run_single_query(query: str) -> tuple[str, str, list]:
    """Single-shot query for the FastAPI endpoint. Uses singleton state."""
    state = await get_state()
    route = await route_query(state.router, query)
    resp = await state.specialists[route].run(user_message(query))

    provider_map = {
        "politicas": state._hr_search,
        "runbooks": state._marketing_search,
        "herramientas": state._products_search,
    }
    provider = provider_map[route]
    sources = [_serialize_annotation(ann) for ann in (provider.last_references or [])]

    return route, resp.text or "", sources


async def run_orchestrator():
    async with DefaultAzureCredential() as credential:
        client = OpenAIChatCompletionClient(
            model=MODEL,
            azure_endpoint=OPENAI_ENDPOINT,
            credential=credential,
            api_version="2024-12-01-preview",
        )
        async with (
            AzureAISearchContextProvider(
                "hr-search",
                endpoint=SEARCH_ENDPOINT,
                credential=credential,
                mode="agentic",
                knowledge_base_name=KB_POLITICAS,
                retrieval_reasoning_effort="low",
                knowledge_base_output_mode="answer_synthesis",
            ) as hr_search,
            AzureAISearchContextProvider(
                "marketing-search",
                endpoint=SEARCH_ENDPOINT,
                credential=credential,
                mode="agentic",
                knowledge_base_name=KB_RUNBOOKS,
                retrieval_reasoning_effort="low",
                knowledge_base_output_mode="answer_synthesis",
            ) as marketing_search,
            AzureAISearchContextProvider(
                "products-search",
                endpoint=SEARCH_ENDPOINT,
                credential=credential,
                mode="agentic",
                knowledge_base_name=KB_HERRAMIENTAS,
                retrieval_reasoning_effort="low",
                knowledge_base_output_mode="answer_synthesis",
            ) as products_search,
        ):
            router = Agent(client=client, instructions=ROUTER_INSTRUCTIONS)

            specialists = {
                "politicas": Agent(client=client, context_providers=[hr_search], instructions=POLITICAS_INSTRUCTIONS),
                "runbooks": Agent(client=client, context_providers=[marketing_search], instructions=RUNBOOKS_INSTRUCTIONS),
                "herramientas": Agent(client=client, context_providers=[products_search], instructions=HERRAMIENTAS_INSTRUCTIONS),
            }

            print("\n Multi-Agent Orchestrator with KB Grounding")
            print("=" * 55)
            print("Type 'quit' to exit\n")

            while True:
                query = input("Question: ").strip()
                if not query:
                    continue
                if query.lower() in ["quit", "exit", "q"]:
                    print("\nGoodbye!")
                    return

                route = await route_query(router, query)
                print(f"Routing to: {route.upper()} agent")

                resp = await specialists[route].run(user_message(query))
                print(f"\nResponse:\n{resp.text}\n")
                print("-" * 55)


if __name__ == "__main__":
    asyncio.run(run_orchestrator())
