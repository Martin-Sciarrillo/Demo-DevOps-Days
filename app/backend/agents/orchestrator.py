import asyncio
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[3] / ".env")
from azure.identity.aio import DefaultAzureCredential

from agent_framework import Agent, Message, Content
from agent_framework_openai import OpenAIChatCompletionClient
from agent_framework.azure import AzureAISearchContextProvider

from config import OPENAI_ENDPOINT, SEARCH_ENDPOINT, MODEL, HR_INDEX, MKT_INDEX, PRD_INDEX, KB_POLITICAS, KB_RUNBOOKS, KB_HERRAMIENTAS

HR_INSTRUCTIONS = """Sos el Agente de Políticas DevOps de DevOps Days CORP.
Respondé preguntas sobre políticas de on-call, rotaciones de guardia, niveles de severidad de incidentes, SLAs/SLOs,
proceso de postmortem, cultura blameless, compensación de guardia y certificaciones usando la base de conocimiento.
Respondé siempre en castellano rioplatense. Sé específico y citá las fuentes cuando sea posible."""

MARKETING_INSTRUCTIONS = """Sos el Agente de Runbooks de DevOps Days CORP.
Respondé preguntas sobre runbooks operacionales, playbooks de incidentes, procedimientos de respuesta a alertas
y pasos de troubleshooting usando la base de conocimiento.
Respondé siempre en castellano rioplatense. Sé específico, listá los pasos y citá las fuentes."""

PRODUCTS_INSTRUCTIONS = """Sos el Agente de Herramientas de DevOps Days CORP.
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
        self._hr_search = AzureAISearchContextProvider(
            "hr-search", endpoint=SEARCH_ENDPOINT,
            credential=self._credential, mode="agentic",
            knowledge_base_name=KB_POLITICAS, retrieval_reasoning_effort="medium",
        )
        self._marketing_search = AzureAISearchContextProvider(
            "marketing-search", endpoint=SEARCH_ENDPOINT,
            credential=self._credential, mode="agentic",
            knowledge_base_name=KB_RUNBOOKS, retrieval_reasoning_effort="medium",
        )
        self._products_search = AzureAISearchContextProvider(
            "products-search", endpoint=SEARCH_ENDPOINT,
            credential=self._credential, mode="agentic",
            knowledge_base_name=KB_HERRAMIENTAS, retrieval_reasoning_effort="medium",
        )
        self.router = Agent(client=self._client, instructions=ROUTER_INSTRUCTIONS)
        self.specialists = {
            "politicas": Agent(client=self._client, context_providers=[self._hr_search], instructions=HR_INSTRUCTIONS),
            "runbooks": Agent(client=self._client, context_providers=[self._marketing_search], instructions=MARKETING_INSTRUCTIONS),
            "herramientas": Agent(client=self._client, context_providers=[self._products_search], instructions=PRODUCTS_INSTRUCTIONS),
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


async def run_single_query(query: str) -> tuple[str, str, list]:
    """Single-shot query for the FastAPI endpoint. Uses singleton state."""
    state = await get_state()
    route = await route_query(state.router, query)
    resp = await state.specialists[route].run(user_message(query))
    return route, resp.text or "", []


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
                retrieval_reasoning_effort="medium",
            ) as hr_search,
            AzureAISearchContextProvider(
                "marketing-search",
                endpoint=SEARCH_ENDPOINT,
                credential=credential,
                mode="agentic",
                knowledge_base_name=KB_RUNBOOKS,
                retrieval_reasoning_effort="medium",
            ) as marketing_search,
            AzureAISearchContextProvider(
                "products-search",
                endpoint=SEARCH_ENDPOINT,
                credential=credential,
                mode="agentic",
                knowledge_base_name=KB_HERRAMIENTAS,
                retrieval_reasoning_effort="medium",
            ) as products_search,
        ):
            router = Agent(client=client, instructions=ROUTER_INSTRUCTIONS)

            specialists = {
                "politicas": Agent(client=client, context_providers=[hr_search], instructions=HR_INSTRUCTIONS),
                "runbooks": Agent(client=client, context_providers=[marketing_search], instructions=MARKETING_INSTRUCTIONS),
                "herramientas": Agent(client=client, context_providers=[products_search], instructions=PRODUCTS_INSTRUCTIONS),
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
