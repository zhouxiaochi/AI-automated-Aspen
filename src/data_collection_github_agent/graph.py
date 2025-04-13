# graph.py
import asyncio
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from utils.load_mcp_config import load_mcp_config
from src.data_collection_github_agent.prompt import DATA_COLLECTION_PROMPT

# use dot env to get the api key and base url (from .env file), override the default ones
load_dotenv()
mcp_config = load_mcp_config()
model = ChatOpenAI(model="gpt-4o-mini", 
                   base_url=os.getenv("BASE_URL"), 
                   api_key=os.getenv("API_KEY"))

@asynccontextmanager
async def make_graph():
    async with MultiServerMCPClient(
        mcp_config
    ) as client:
        agent = create_react_agent(model, client.get_tools())
        yield agent

async def main():
    async with make_graph() as agent:
        for page_number in range(1, 3):
            print(f"Collecting files from page {page_number}")
            result = await agent.ainvoke({"messages": DATA_COLLECTION_PROMPT.format(per_page=20, page_number=page_number)})
            print(result["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())
