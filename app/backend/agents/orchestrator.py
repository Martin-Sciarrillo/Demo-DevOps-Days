import asyncio
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[3] / ".env")
from azure.identity.aio import DefaultAzureCredential

from agent_framework import Agent, Message, Content
from agent_framework_openai import OpenAIChatCompletionClient
from agent_framework.azure import AzureAISearchContextProvider

from config import OPENAI_ENDPOINT, SEARCH_ENDPOINT, MODEL, HR_INDEX, MKT_INDEX, PRD_INDEX

HR_INSTRUCTIONS = """Sos el Agente Especialista de RR.HH. de DevOps Days CORP.
Respondé preguntas sobre políticas de RR.HH., vacaciones, beneficios y el manual del empleado usando la base de conocimiento.
Respondé siempre en castellano rioplatense. Sé específico y citá las fuentes cuando sea posible."""

MARKETING_INSTRUCTIONS = """Sos el Agente Especialista de Marketing de DevOps Days CORP.
Respondé preguntas sobre campañas de marketing, lineamientos de marca y estrategias usando la base de conocimiento.
Respondé siempre en castellano rioplatense. Sé específico y citá las fuentes cuando sea posible."""

PRODUCTS_INSTRUCTIONS = """Sos el Agente Especialista de Productos de DevOps Days CORP.
Respondé preguntas sobre el catálogo de productos, especificaciones y precios usando la base de conocimiento.
Respondé siempre en castellano rioplatense. Sé específico y citá las fuentes cuando sea posible."""

ROUTER_INSTRUCTIONS = """Sos un agente de enrutamiento. Analizá la consulta del usuario y determiná qué especialista debe manejarla.

Respondé ÚNICAMENTE con uno de estos nombres:
- "hr"
- "marketing"
- "products"

Solo respondé con el nombre del agente, nada más."""


def user_message(text: str) -> Message:
    return Message(role="user", contents=[Content.from_text(text)])


async def route_query(router: Agent, query: str) -> str:
    resp = await router.run(user_message(query))
    route = (resp.text or "").strip().lower()
    if "hr" in route:
        return "hr"
    if "marketing" in route or "brand" in route or "campaign" in route:
        return "marketing"
    if "product" in route:
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
