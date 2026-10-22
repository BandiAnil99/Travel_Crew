"""Validated budget calculator exposed as a LangChain tool."""
import math
from langchain_core.tools import tool


@tool
def calculate_trip_budget(
    transportation: float, accommodation: float, meals: float,
    attractions: float, miscellaneous: float, travelers: int, budget: float,
) -> dict:
    """Add estimated expense categories, calculate per-person cost, and compare with budget."""
    values = [transportation, accommodation, meals, attractions, miscellaneous, budget]
    if travelers < 1 or any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Travelers must be positive and all costs/budget must be non-negative.")
    total = sum(values[:5])
    return {
        "categories": {
            "transportation": transportation, "accommodation": accommodation,
            "meals": meals, "attractions": attractions, "miscellaneous": miscellaneous,
        },
        "total": round(total, 2), "per_traveler": round(total / travelers, 2),
        "budget": budget, "remaining": round(budget - total, 2),
        "within_budget": total <= budget,
    }
