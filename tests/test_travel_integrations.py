from datetime import date, timedelta

import travel_integrations


def test_tavily_search_uses_configured_api_key(monkeypatch):
    requests = []
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    monkeypatch.setattr(
        travel_integrations,
        "_request_json",
        lambda url, **kwargs: requests.append((url, kwargs)) or {"results": []},
    )

    result = travel_integrations.search_destination("Kyoto temples")

    assert result == {"results": []}
    assert requests[0][0] == "https://api.tavily.com/search"
    assert requests[0][1]["payload"]["api_key"] == "test-key"
    assert requests[0][1]["payload"]["query"] == "Kyoto temples"


def test_weather_marks_dates_beyond_forecast_window_unavailable(monkeypatch):
    def unexpected_api_call(*args, **kwargs):
        raise AssertionError("The service should not be called outside its forecast window.")

    monkeypatch.setattr(travel_integrations, "_request_json", unexpected_api_call)
    start = date.today() + timedelta(days=17)

    result = travel_integrations.get_weather("Kyoto", start, start + timedelta(days=2))

    assert result["available"] is False


def test_driving_route_converts_osrm_distance_and_duration(monkeypatch):
    responses = iter(
        [
            {"results": [{"latitude": 35.0, "longitude": 139.0}]},
            {"results": [{"latitude": 36.0, "longitude": 140.0}]},
            {"routes": [{"distance": 125_500, "duration": 7_200}]},
        ]
    )
    monkeypatch.setattr(travel_integrations, "_request_json", lambda *args, **kwargs: next(responses))

    result = travel_integrations.get_driving_route("Tokyo", "Kyoto")

    assert result["distance_km"] == 125.5
    assert result["duration_hours"] == 2.0
    assert "does not represent a flight" in result["note"]
