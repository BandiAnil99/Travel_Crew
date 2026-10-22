"""Dependency-free validation and estimate helpers for the travel planner."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import math
from typing import Any


@dataclass(frozen=True)
class TripRequest:
    destination: str
    starting_location: str
    start_date: date
    end_date: date
    budget: float
    currency: str
    interests: tuple[str, ...]

    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days + 1

    @property
    def nights(self) -> int:
        return max(self.duration_days - 1, 0)

    def validate(self) -> None:
        if not self.destination.strip() or len(self.destination) > 120:
            raise ValueError("Enter a destination between 1 and 120 characters.")
        if not self.starting_location.strip() or len(self.starting_location) > 120:
            raise ValueError("Enter a starting location between 1 and 120 characters.")
        if self.start_date < date.today():
            raise ValueError("The departure date cannot be in the past.")
        if self.end_date < self.start_date:
            raise ValueError("The return date must be on or after the start date.")
        if self.duration_days > 31:
            raise ValueError("Trips are limited to 31 days.")
        if not math.isfinite(self.budget) or self.budget <= 0:
            raise ValueError("The total budget must be greater than zero.")
        if self.currency not in {"USD", "INR", "EUR", "GBP"}:
            raise ValueError("Choose a supported currency.")
        if not self.interests:
            raise ValueError("Choose at least one travel interest.")


# Illustrative prototype rates per person; these are not live booking prices.
DAILY_SAMPLE_RATES: dict[str, dict[str, float]] = {
    "USD": {"hotel": 85, "food": 35, "local_transport": 18, "activities": 25},
    "INR": {"hotel": 4500, "food": 1800, "local_transport": 700, "activities": 1200},
    "EUR": {"hotel": 80, "food": 32, "local_transport": 16, "activities": 23},
    "GBP": {"hotel": 70, "food": 28, "local_transport": 14, "activities": 20},
}


def estimate_trip_costs(days: int, nights: int, currency: str) -> dict[str, Any]:
    """Return illustrative low, standard, and comfort estimates for one traveler."""
    if days < 1 or nights < 0 or nights > days:
        raise ValueError("Days and nights must describe a valid trip.")
    if currency not in DAILY_SAMPLE_RATES:
        raise ValueError("Choose a supported currency.")

    rates = DAILY_SAMPLE_RATES[currency]
    categories = {
        "accommodation": rates["hotel"] * nights,
        "food": rates["food"] * days,
        "local_transport": rates["local_transport"] * days,
        "activities": rates["activities"] * days,
    }
    low_categories = {
        "accommodation": rates["hotel"] * 0.65 * nights,
        "food": rates["food"] * 0.8 * days,
        "local_transport": rates["local_transport"] * 0.75 * days,
        "activities": rates["activities"] * 0.5 * days,
    }
    standard = sum(categories.values())
    # Less-expensive alternatives assume shared/basic accommodation and free activities.
    low = sum(low_categories.values())
    comfort = standard * 1.55
    return {
        "currency": currency,
        "traveler_count": 1,
        "rates_are_illustrative": True,
        "categories": {name: round(amount, 2) for name, amount in categories.items()},
        "low_cost_categories": {name: round(amount, 2) for name, amount in low_categories.items()},
        "low": round(low, 2),
        "standard": round(standard, 2),
        "comfort": round(comfort, 2),
    }


def build_day_schedule(start_date: date, days: int) -> list[dict[str, str | int]]:
    if days < 1 or days > 31:
        raise ValueError("Trip duration must be between 1 and 31 days.")
    return [
        {
            "day": index + 1,
            "date": (start_date + timedelta(days=index)).isoformat(),
            "weekday": (start_date + timedelta(days=index)).strftime("%A"),
        }
        for index in range(days)
    ]
