from .prompts import AGENTS
from tools.web_search import search_travel_information

SPEC = AGENTS["researcher"]
TOOLS = [search_travel_information]
