import asyncio
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[3] / ".env")
from azure.identity.aio import DefaultAzureCredential

from agent_framework import Agent, Message, Content
from agent_framework_openai import OpenAIChatCompletionClient
from agent_framework.azure import AzureAISearchContextProvider

from config import OPENAI_ENDPOINT, SEARCH_ENDPOINT, MODEL, HR_INDEX, MKT_INDEX, PRD_INDEX

HR_INSTRUCTIONS = """You are an HR Specialist Agent for Zava Corporation.
Answer questions about HR policies, PTO, benefits, and employee handbook using the knowledge base.
Be specific and cite sources when possible."""

MARKETING_INSTRUCTIONS = """You are a Marketing Specialist Agent for Zava Corporation.
Answer questions about marketing campaigns, brand guidelines, and marketing strategies using the knowledge base.
Be specific and cite sources when possible."""

PRODUCTS_INSTRUCTIONS = """You are a Products Specialist Agent for Zava Corporation.
Answer questions about products, catalog, specifications, and pricing using the knowledge base.
Be specific and cite sources when possible."""

ROUTER_INSTRUCTIONS = """You are a routing agent. Analyze the user query and determine which specialist should handle it.

Respond with ONLY one of these agent names:
- "hr"
- "marketing"
- "products"

Just respond with the agent name, nothing else."""


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
