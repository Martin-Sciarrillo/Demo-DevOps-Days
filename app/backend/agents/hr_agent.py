"""HR Agent - Connected to kb1-hr Knowledge Base."""

import asyncio
from azure.identity.aio import DefaultAzureCredential

from agent_framework import Agent, Message, Content
from agent_framework.azure import AzureAIAgentClient, AzureAISearchContextProvider

from config import SEARCH_ENDPOINT, PROJECT_ENDPOINT, MODEL, HR_KB_NAME

HR_INSTRUCTIONS = """You are an HR Specialist Agent for Zava Corporation.
Answer questions about HR policies, PTO, benefits, and employee handbook using the knowledge base.
Be specific and cite sources when possible."""


async def run_hr_agent(query: str) -> str:
    """Run the HR agent with a query."""
    async with DefaultAzureCredential() as credential:
        async with (
            AzureAIAgentClient(
                project_endpoint=PROJECT_ENDPOINT,
                model_deployment_name=MODEL,
                credential=credential,
            ) as client,
            AzureAISearchContextProvider(
                endpoint=SEARCH_ENDPOINT,
                knowledge_base_name=HR_KB_NAME,
                credential=credential,
                mode="agentic",
                knowledge_base_output_mode="answer_synthesis",
            ) as kb_context,
        ):
            agent = Agent(
                client=client,
                context_provider=kb_context,
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
