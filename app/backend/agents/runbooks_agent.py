"""Agente de Runbooks — conectado a kb-runbooks."""

import asyncio
from azure.identity.aio import DefaultAzureCredential

from agent_framework import Agent, Message, Content
from agent_framework_openai import OpenAIChatCompletionClient
from agent_framework.azure import AzureAISearchContextProvider

from config import OPENAI_ENDPOINT, SEARCH_ENDPOINT, MODEL, INDEX_RUNBOOKS

RUNBOOKS_INSTRUCTIONS = """Sos el Agente de Runbooks de DevOps Days CORP.
Respondé preguntas sobre runbooks operacionales, playbooks de incidentes, procedimientos de respuesta a alertas
y pasos de troubleshooting usando la base de conocimiento.
Respondé siempre en castellano rioplatense. Sé específico, listá los pasos y citá las fuentes."""


async def run_runbooks_agent(query: str) -> str:
    """Run the Runbooks agent with a query."""
    async with DefaultAzureCredential() as credential:
        client = OpenAIChatCompletionClient(model=MODEL, azure_endpoint=OPENAI_ENDPOINT, credential=credential, api_version="2024-12-01-preview")
        async with (
            AzureAISearchContextProvider(
                "runbooks-search",
                endpoint=SEARCH_ENDPOINT,
                index_name=INDEX_RUNBOOKS,
                credential=credential,
                mode="semantic",
                semantic_configuration_name="default",
            ) as kb_context,
        ):
            agent = Agent(
                client=client,
                context_providers=[kb_context],
                instructions=RUNBOOKS_INSTRUCTIONS,
            )
            message = Message(role="user", contents=[Content.from_text(query)])
            response = await agent.run(message)
            return response.text


async def main():
    print("\nAgente de Runbooks (kb-runbooks)")
    print("=" * 50)

    query = "¿Cómo resuelvo un CrashLoopBackOff en EKS?"
    print(f"\nQuery: {query}")

    response = await run_runbooks_agent(query)
    print(f"\nResponse:\n{response}")


if __name__ == "__main__":
    asyncio.run(main())
