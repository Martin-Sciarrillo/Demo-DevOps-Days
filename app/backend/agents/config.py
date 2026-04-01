"""Shared configuration for all agents. Values come from environment variables."""

import os

SEARCH_ENDPOINT = os.getenv(
    "AZURE_SEARCH_ENDPOINT",
    "https://srch-jnlr3ry4yf2o6.search.windows.net",
)

PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")

MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

HR_KB_NAME = "kb1-hr"
MKT_KB_NAME = "kb2-marketing"
PRD_KB_NAME = "kb3-products"

HR_SOURCE_ID = os.getenv("KB1_HR_SOURCE_ID", HR_KB_NAME)
MKT_SOURCE_ID = os.getenv("KB2_MARKETING_SOURCE_ID", MKT_KB_NAME)
PRD_SOURCE_ID = os.getenv("KB3_PRODUCTS_SOURCE_ID", PRD_KB_NAME)
