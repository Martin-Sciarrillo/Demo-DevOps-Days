"""Agente de Herramientas — conectado a kb-herramientas."""

import asyncio
from azure.identity.aio import DefaultAzureCredential

from agent_framework import Agent, Message, Content
from agent_framework_openai import OpenAIChatCompletionClient
from agent_framework.azure import AzureAISearchContextProvider

from config import OPENAI_ENDPOINT, SEARCH_ENDPOINT, MODEL, INDEX_HERRAMIENTAS

HERRAMIENTAS_INSTRUCTIONS = """Sos el Agente de Herramientas de DevOps Days CORP.
Respondé preguntas sobre el catálogo de herramientas internas: plataformas de infraestructura, CI/CD, monitoring,
observabilidad, seguridad y gestión de secretos usando la base de conocimiento.
Respondé siempre en castellano rioplatense. Sé específico e incluí casos de uso y cómo acceder a cada herramienta."""


async def run_herramientas_agent(query: str) -> str:
    """Run the Herramientas agent with a query."""
    async with DefaultAzureCredential() as credential:
        client = OpenAIChatCompletionClient(model=MODEL, azure_endpoint=OPENAI_ENDPOINT, credential=credential, api_version="2024-12-01-preview")
        async with (
            AzureAISearchContextProvider(
                "herramientas-search",
                endpoint=SEARCH_ENDPOINT,
                index_name=INDEX_HERRAMIENTAS,
                credential=credential,
                mode="semantic",
                semantic_configuration_name="default",
            ) as kb_context,
        ):
            agent = Agent(
                client=client,
                context_providers=[kb_context],
                instructions=HERRAMIENTAS_INSTRUCTIONS,
            )
            message = Message(role="user", contents=[Content.from_text(query)])
            response = await agent.run(message)
            return response.text


async def main():
    print("\nAgente de Herramientas (kb-herramientas)")
    print("=" * 50)

    query = "¿Cómo gestiono secretos con Vault?"
    print(f"\nQuery: {query}")

    response = await run_herramientas_agent(query)
    print(f"\nResponse:\n{response}")


if __name__ == "__main__":
    asyncio.run(main())
