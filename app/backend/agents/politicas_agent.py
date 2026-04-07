"""Agente de Políticas — conectado a kb-politicas."""

import asyncio
from azure.identity.aio import DefaultAzureCredential

from agent_framework import Agent, Message, Content
from agent_framework_openai import OpenAIChatCompletionClient
from agent_framework.azure import AzureAISearchContextProvider

from config import OPENAI_ENDPOINT, SEARCH_ENDPOINT, MODEL, INDEX_POLITICAS

POLITICAS_INSTRUCTIONS = """Sos el Agente de Políticas DevOps de DevOps Days CORP.
Respondé preguntas sobre políticas de on-call, rotaciones de guardia, niveles de severidad de incidentes, SLAs/SLOs,
proceso de postmortem, cultura blameless, compensación de guardia y certificaciones usando la base de conocimiento.
Respondé siempre en castellano rioplatense. Sé específico y citá las fuentes cuando sea posible."""


async def run_politicas_agent(query: str) -> str:
    """Run the Políticas agent with a query."""
    async with DefaultAzureCredential() as credential:
        client = OpenAIChatCompletionClient(model=MODEL, azure_endpoint=OPENAI_ENDPOINT, credential=credential, api_version="2024-12-01-preview")
        async with (
            AzureAISearchContextProvider(
                "politicas-search",
                endpoint=SEARCH_ENDPOINT,
                index_name=INDEX_POLITICAS,
                credential=credential,
                mode="semantic",
                semantic_configuration_name="default",
            ) as kb_context,
        ):
            agent = Agent(
                client=client,
                context_providers=[kb_context],
                instructions=POLITICAS_INSTRUCTIONS,
            )
            message = Message(role="user", contents=[Content.from_text(query)])
            response = await agent.run(message)
            return response.text


async def main():
    print("\nAgente de Políticas (kb-politicas)")
    print("=" * 50)

    query = "¿Cuál es el proceso de postmortem blameless?"
    print(f"\nQuery: {query}")

    response = await run_politicas_agent(query)
    print(f"\nResponse:\n{response}")


if __name__ == "__main__":
    asyncio.run(main())
