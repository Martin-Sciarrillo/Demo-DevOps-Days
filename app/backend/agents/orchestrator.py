import asyncio
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[3] / ".env")
from azure.identity.aio import DefaultAzureCredential

from agent_framework import Agent, Message, Content
from agent_framework_openai import OpenAIChatCompletionClient
from agent_framework.azure import AzureAISearchContextProvider

from config import OPENAI_ENDPOINT, SEARCH_ENDPOINT, MODEL, HR_INDEX, MKT_INDEX, PRD_INDEX

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

- "hr": políticas de on-call, guardia, escalado, SLA, SLO, postmortem, cultura, compensación, certificaciones
- "products": herramientas internas, plataformas, Kubernetes, Terraform, CI/CD, monitoring, observabilidad, secretos
- "marketing": runbooks, playbooks, procedimientos operacionales, cómo resolver alertas, troubleshooting paso a paso

Respondé ÚNICAMENTE con uno de estos nombres: hr, products, marketing
Solo respondé con el nombre del agente, nada más."""


def user_message(text: str) -> Message:
    return Message(role="user", contents=[Content.from_text(text)])


async def route_query(router: Agent, query: str) -> str:
    resp = await router.run(user_message(query))
    route = (resp.text or "").strip().lower()
    if "hr" in route:
        return "hr"
    if "marketing" in route or "runbook" in route or "playbook" in route:
        return "marketing"
    if "product" in route or "tool" in route or "herramienta" in route:
        return "products"
    return "hr"


async def run_single_query(query: str) -> tuple[str, str, list]:
    """Single-shot query for the FastAPI endpoint."""
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
                index_name=HR_INDEX,
                credential=credential,
                mode="semantic",
                semantic_configuration_name="default",
            ) as hr_search,
            AzureAISearchContextProvider(
                "marketing-search",
                endpoint=SEARCH_ENDPOINT,
                index_name=MKT_INDEX,
                credential=credential,
                mode="semantic",
                semantic_configuration_name="default",
            ) as marketing_search,
            AzureAISearchContextProvider(
                "products-search",
                endpoint=SEARCH_ENDPOINT,
                index_name=PRD_INDEX,
                credential=credential,
                mode="semantic",
                semantic_configuration_name="default",
            ) as products_search,
        ):
            router = Agent(client=client, instructions=ROUTER_INSTRUCTIONS)
            specialists = {
                "hr": Agent(client=client, context_providers=[hr_search], instructions=HR_INSTRUCTIONS),
                "marketing": Agent(client=client, context_providers=[marketing_search], instructions=MARKETING_INSTRUCTIONS),
                "products": Agent(client=client, context_providers=[products_search], instructions=PRODUCTS_INSTRUCTIONS),
            }
            route = await route_query(router, query)
            resp = await specialists[route].run(user_message(query))
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
                index_name=HR_INDEX,
                credential=credential,
                mode="semantic",
                semantic_configuration_name="default",
            ) as hr_search,
            AzureAISearchContextProvider(
                "marketing-search",
                endpoint=SEARCH_ENDPOINT,
                index_name=MKT_INDEX,
                credential=credential,
                mode="semantic",
                semantic_configuration_name="default",
            ) as marketing_search,
            AzureAISearchContextProvider(
                "products-search",
                endpoint=SEARCH_ENDPOINT,
                index_name=PRD_INDEX,
                credential=credential,
                mode="semantic",
                semantic_configuration_name="default",
            ) as products_search,
        ):
            router = Agent(client=client, instructions=ROUTER_INSTRUCTIONS)

            specialists = {
                "hr": Agent(client=client, context_providers=[hr_search], instructions=HR_INSTRUCTIONS),
                "marketing": Agent(client=client, context_providers=[marketing_search], instructions=MARKETING_INSTRUCTIONS),
                "products": Agent(client=client, context_providers=[products_search], instructions=PRODUCTS_INSTRUCTIONS),
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
