"""Marketing Agent - Connected to kb2-marketing Knowledge Base."""

import asyncio
from azure.identity.aio import DefaultAzureCredential

from agent_framework import Agent, Message, Content
from agent_framework.azure import AzureOpenAIChatClient, AzureAISearchContextProvider

from config import OPENAI_ENDPOINT, SEARCH_ENDPOINT, MODEL, MKT_KB_NAME

MARKETING_INSTRUCTIONS = """You are a Marketing Specialist Agent for Zava Corporation.
Answer questions about marketing campaigns, brand guidelines, and marketing strategies using the knowledge base.
Be specific and cite sources when possible."""


async def run_marketing_agent(query: str) -> str:
    """Run the Marketing agent with a query."""
    async with DefaultAzureCredential() as credential:
        client = AzureOpenAIChatClient(endpoint=OPENAI_ENDPOINT, deployment_name=MODEL, credential=credential)
        async with (
            AzureAISearchContextProvider(
                endpoint=SEARCH_ENDPOINT,
                knowledge_base_name=MKT_KB_NAME,
                credential=credential,
                mode="agentic",
                knowledge_base_output_mode="answer_synthesis",
            ) as kb_context,
        ):
            agent = Agent(
                client=client,
                context_provider=kb_context,
                instructions=MARKETING_INSTRUCTIONS,
            )
            message = Message(role="user", contents=[Content.from_text(query)])
            response = await agent.run(message)
            return response.text


async def main():
    print("\n Marketing Agent (kb2-marketing)")
    print("=" * 50)

    query = "What are our current marketing campaigns?"
    print(f"\nQuery: {query}")

    response = await run_marketing_agent(query)
    print(f"\nResponse:\n{response}")


if __name__ == "__main__":
    asyncio.run(main())
