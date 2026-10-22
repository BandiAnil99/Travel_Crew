from datetime import date, timedelta

import pytest

from travel_core import TripRequest, build_day_schedule, estimate_trip_costs


def valid_request(**overrides):
    values = {
        "destination": "Kyoto",
        "starting_location": "Tokyo",
        "start_date": date.today() + timedelta(days=10),
        "end_date": date.today() + timedelta(days=13),
        "budget": 100_000,
        "currency": "INR",
        "interests": ("Culture",),
    }
    values.update(overrides)
    return TripRequest(**values)


def test_request_duration_counts_both_travel_dates():
    request = valid_request()
    assert request.duration_days == 4
    assert request.nights == 3


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"destination": " "}, "destination"),
        ({"start_date": date.today() - timedelta(days=1)}, "past"),
        ({"end_date": date.today() + timedelta(days=9)}, "return date"),
        ({"budget": 0}, "budget"),
        ({"interests": ()}, "interest"),
        ({"currency": "CAD"}, "currency"),
        ({"end_date": date.today() + timedelta(days=41)}, "31 days"),
    ],
)
def test_request_validation_rejects_invalid_input(overrides, message):
    with pytest.raises(ValueError, match=message):
        valid_request(**overrides).validate()


@pytest.mark.parametrize("budget", [float("nan"), float("inf"), float("-inf")])
def test_request_validation_rejects_non_finite_budget(budget):
    with pytest.raises(ValueError, match="budget"):
        valid_request(budget=budget).validate()


def test_budget_estimate_is_ordered_and_currency_labeled():
    result = estimate_trip_costs(days=4, nights=3, currency="INR")
    assert result["currency"] == "INR"
    assert result["traveler_count"] == 1
    assert result["rates_are_illustrative"] is True
    assert result["low"] < result["standard"] < result["comfort"]
    assert set(result["categories"]) == {"accommodation", "food", "local_transport", "activities"}
    assert set(result["low_cost_categories"]) == set(result["categories"])
    assert sum(result["low_cost_categories"].values()) == result["low"]


def test_budget_estimate_rejects_invalid_duration():
    with pytest.raises(ValueError, match="valid trip"):
        estimate_trip_costs(days=2, nights=3, currency="USD")


def test_schedule_includes_each_date_and_weekday():
    schedule = build_day_schedule(date(2027, 4, 1), 3)
    assert [item["date"] for item in schedule] == ["2027-04-01", "2027-04-02", "2027-04-03"]
    assert [item["day"] for item in schedule] == [1, 2, 3]


def test_schedule_rejects_duration_outside_supported_range():
    with pytest.raises(ValueError, match="between 1 and 31"):
        build_day_schedule(date(2027, 4, 1), 32)
