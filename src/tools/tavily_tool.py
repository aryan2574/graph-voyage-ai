import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def tavily_search(query):
    # Returns a Python dictionary
    response = client.search(query=query, max_results=5)

    formatted_results = []

    for i, r in enumerate(response.get("results", []), start=1):
        title = r.get("title", "Unknown")
        url = r.get("url", "")
        snippet = r.get("content", "").strip()

        # Truncate clean text snippets to ~300 chars
        if len(snippet) > 300:
            snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

        formatted_results.append(f"{i}. **{title}**\n   URL: {url}\n   {snippet}")

    return "\n\n".join(formatted_results)