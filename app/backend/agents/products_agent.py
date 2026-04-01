"""Products Agent - Connected to kb3-products Knowledge Base."""

import asyncio
from azure.identity.aio import DefaultAzureCredential

from agent_framework import Agent, Message, Content
from agent_framework_openai import OpenAIChatCompletionClient
from agent_framework.azure import AzureAISearchContextProvider

from config import OPENAI_ENDPOINT, SEARCH_ENDPOINT, MODEL, PRD_INDEX

PRODUCTS_INSTRUCTIONS = """Sos el Agente Especialista de Productos de DevOps Days CORP.
Respondé preguntas sobre el catálogo de productos, especificaciones y precios usando la base de conocimiento.
Respondé siempre en castellano rioplatense. Sé específico y citá las fuentes cuando sea posible."""


async def run_products_agent(query: str) -> str:
    """Run the Products agent with a query."""
    async with DefaultAzureCredential() as credential:
        client = OpenAIChatCompletionClient(model=MODEL, azure_endpoint=OPENAI_ENDPOINT, credential=credential, api_version="2024-12-01-preview")
        async with (
            AzureAISearchContextProvider(
                "products-search",
                endpoint=SEARCH_ENDPOINT,
                index_name=PRD_INDEX,
                credential=credential,
                mode="semantic",
                semantic_configuration_name="default",
            ) as kb_context,
        ):
            agent = Agent(
                client=client,
                context_providers=[kb_context],
                instructions=PRODUCTS_INSTRUCTIONS,
            )
            message = Message(role="user", contents=[Content.from_text(query)])
            response = await agent.run(message)
            return response.text


async def main():
    print("\n Products Agent (kb3-products)")
    print("=" * 50)

    query = "What products do you offer?"
    print(f"\nQuery: {query}")

    response = await run_products_agent(query)
    print(f"\nResponse:\n{response}")


if __name__ == "__main__":
    asyncio.run(main())
