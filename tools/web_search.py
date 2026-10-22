"""Live web search tool. Empty/error cases are explicit and never replaced with invented results."""
import os
from langchain_core.tools import tool
from travel_integrations import IntegrationError, search_destination


@tool
def search_travel_information(query: str) -> dict:
    """Search current web sources for attractions, local transport, opening information, and travel advice; include source URLs."""
    if not query.strip():
        raise ValueError("Search query cannot be empty.")
    try:
        response = search_destination(query)
    except IntegrationError as exc:
        return {"status": "unavailable", "message": str(exc), "results": []}
    if "results" in response:
        results = response.get("results") or []
        return {"status": "ok" if results else "empty", "provider": "Tavily", "results": results}
    items = response.get("query", {}).get("search", [])
    return {
        "status": "ok" if items else "empty", "provider": "Wikimedia",
        "results": [{"title": x.get("title"), "url": "https://en.wikipedia.org/wiki/" + x.get("title", "").replace(" ", "_"), "content": x.get("snippet", "")} for x in items],
    }
