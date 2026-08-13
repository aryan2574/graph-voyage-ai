import os
import certifi
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()


TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

client = MultiServerMCPClient(
    {
        "tavily" : {
            "transport" : "streamable_http",
            "url" : f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
        },
        # Remote aviationstack mcp - from pipeworx
        # "aviationstack": {
        #     "transport": "streamable_http",
        #     "url": "https://gateway.pipeworx.io/aviationstack/mcp"
        # },
        # Local aviationstack mcp
        # "aviationstack": {
        #     "transport" : "stdio",
        #     "command": "uvx",
        #     "args": [
        #         "aviationstack-mcp"
        #     ],
        #     "env": {
        #         "AVIATION_STACK_API_KEY": AVIATIONSTACK_API_KEY
        #     }
        # }
    }
)

# Print the list of all available tools
async def get_all_tools():
    tools = await client.get_tools()
    print("\nAvailable MCP Tools:\n")

    for tool in tools:
        print(tool.name)


# Get tavily_search tool object
tavily_search_tool = None

async def get_tavily_search_tool():
    global tavily_search_tool
    if tavily_search_tool is not None:
        return 
    
    tools = await client.get_tools()

    tavily_search_tool = next(
        tool
        for tool in tools
        if(tool.name == "tavily_search")
    )


# Call tavily_search_tool with a query
async def tavily_mcp_search(query: str):
    await get_tavily_search_tool()
    result = await tavily_search_tool.ainvoke(
        {
            "query": query
        }
    )
    return result
