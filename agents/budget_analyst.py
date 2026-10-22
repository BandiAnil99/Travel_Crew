from .prompts import AGENTS
from tools.calculator import calculate_trip_budget

SPEC = AGENTS["budget"]
TOOLS = [calculate_trip_budget]
