"""HR Agent - Connected to kb1-hr Knowledge Base."""

import asyncio
from azure.identity.aio import DefaultAzureCredential

from agent_framework import Agent, Message, Content
from agent_framework_openai import OpenAIChatCompletionClient
from agent_framework.azure import AzureAISearchContextProvider

from config import OPENAI_ENDPOINT, SEARCH_ENDPOINT, MODEL, HR_INDEX

HR_INSTRUCTIONS = """Sos el Agente Especialista de RR.HH. de DevOps Days CORP.
Respondé preguntas sobre políticas de RR.HH., vacaciones, beneficios y el manual del empleado usando la base de conocimiento.
Respondé siempre en castellano rioplatense. Sé específico y citá las fuentes cuando sea posible."""


async def run_hr_agent(query: str) -> str:
    """Run the HR agent with a query."""
    async with DefaultAzureCredential() as credential:
        client = OpenAIChatCompletionClient(model=MODEL, azure_endpoint=OPENAI_ENDPOINT, credential=credential, api_version="2024-12-01-preview")
        async with (
            AzureAISearchContextProvider(
                "hr-search",
                endpoint=SEARCH_ENDPOINT,
                index_name=HR_INDEX,
                credential=credential,
                mode="semantic",
                semantic_configuration_name="default",
            ) as kb_context,
        ):
            agent = Agent(
                client=client,
                context_providers=[kb_context],
                instructions=HR_INSTRUCTIONS,
            )
            message = Message(role="user", contents=[Content.from_text(query)])
            response = await agent.run(message)
            return response.text


async def main():
    print("\n HR Agent (kb1-hr)")
    print("=" * 50)

    query = "What is the PTO policy?"
    print(f"\nQuery: {query}")

    response = await run_hr_agent(query)
    print(f"\nResponse:\n{response}")


if __name__ == "__main__":
    asyncio.run(main())
