"""Small, rate-conscious clients for public travel information APIs."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from typing import Any

USER_AGENT = "SmartTravelPlanner/1.0 (prototype; respectful public API usage)"


class IntegrationError(RuntimeError):
    """An external travel information service could not complete a request."""


def _request_json(
    url: str, *, method: str = "GET", payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None
) -> dict[str, Any]:
    request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise IntegrationError(f"Travel information service request failed: {exc}") from exc
    if not isinstance(result, dict):
        raise IntegrationError("Travel information service returned an unexpected response.")
    return result


def search_destination(query: str) -> dict[str, Any]:
    """Search Tavily when configured; otherwise use Wikimedia's public search API."""
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if api_key:
        return _request_json(
            "https://api.tavily.com/search",
            method="POST",
            payload={"api_key": api_key, "query": query, "search_depth": "basic", "max_results": 5},
        )

    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 5,
        }
    )
    return _request_json(url)


def _geocode(place: str) -> dict[str, Any]:
    url = "https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode(
        {"name": place, "count": 1, "language": "en", "format": "json"}
    )
    result = _request_json(url)
    matches = result.get("results") or []
    if not matches:
        raise IntegrationError(f"No coordinates found for {place!r}.")
    return matches[0]


def get_weather(destination: str, start_date: date, end_date: date) -> dict[str, Any]:
    """Fetch a forecast when the requested dates are within Open-Meteo's horizon."""
    today = date.today()
    days_ahead = (start_date - today).days
    if days_ahead < 0 or (end_date - today).days > 15:
        return {
            "available": False,
            "message": "Forecast not available: Open-Meteo forecasts cover today through 16 days ahead.",
        }
    place = _geocode(destination)
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "auto",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
    )
    forecast = _request_json(url)
    return {
        "available": True,
        "location": f"{place.get('name', destination)}, {place.get('country', '')}".strip(", "),
        "forecast": forecast.get("daily", {}),
        "source": "Open-Meteo (https://open-meteo.com/)",
    }


def get_driving_route(origin: str, destination: str) -> dict[str, Any]:
    """Get a public OSRM driving estimate; it is not a flight or transit quote."""
    origin_location = _geocode(origin)
    destination_location = _geocode(destination)
    coordinates = (
        f"{origin_location['longitude']},{origin_location['latitude']};"
        f"{destination_location['longitude']},{destination_location['latitude']}"
    )
    result = _request_json(f"https://router.project-osrm.org/route/v1/driving/{coordinates}?overview=false")
    routes = result.get("routes") or []
    if not routes:
        raise IntegrationError("No driving route was found for these locations.")
    route = routes[0]
    return {
        "origin": origin,
        "destination": destination,
        "distance_km": round(route["distance"] / 1000, 1),
        "duration_hours": round(route["duration"] / 3600, 1),
        "source": "OSRM public routing demo (https://project-osrm.org/)",
        "note": "Driving estimate only; it does not represent a flight, public transit, or a ticket quote.",
    }
