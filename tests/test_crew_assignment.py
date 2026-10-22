from datetime import date, timedelta
import json
from pathlib import Path
import pytest

from main import run, sample_trip, save_outputs
from tools.calculator import calculate_trip_budget
from tools.web_search import search_travel_information
import travel_integrations

def test_calculator_total_and_per_person():
    result = calculate_trip_budget.invoke({"transportation":100,"accommodation":200,"meals":90,"attractions":60,"miscellaneous":50,"travelers":2,"budget":600})
    assert result["total"] == 500
    assert result["per_traveler"] == 250
    assert result["remaining"] == 100
    assert result["within_budget"] is True

@pytest.mark.parametrize("field,value", [("travelers",0),("meals",-1),("budget",-1)])
def test_calculator_rejects_invalid_inputs(field,value):
    args={"transportation":1,"accommodation":1,"meals":1,"attractions":1,"miscellaneous":1,"travelers":1,"budget":10}
    args[field]=value
    with pytest.raises(ValueError): calculate_trip_budget.invoke(args)

def test_search_handles_empty_results(monkeypatch):
    monkeypatch.setattr("tools.web_search.search_destination",lambda query:{"results":[]})
    result=search_travel_information.invoke({"query":"Jaipur attractions"})
    assert result["status"]=="empty" and result["results"]==[]

def test_context_flows_and_critic_causes_bounded_revision():
    state=run(sample_trip(),offline=True)
    assert state["revision_count"]==1
    assert state["approved"] is True
    assert any("Link A" in x for x in state["trace"])
    assert any("Link B" in x for x in state["trace"])
    assert any("Link C" in x for x in state["trace"])
    assert "Revision:" in state["itinerary"]

def test_critic_revision_loop_stops_after_two_revisions(monkeypatch):
    import main
    class RejectingModel:
        def invoke(self, prompt):
            return type("Response", (), {"content": '{"approved": false, "issues": ["Review remains unresolved"]}'})()
    monkeypatch.setattr(main, "search_travel_information", type("ToolMock", (), {"invoke":lambda self,args: {"status":"empty", "results":[]}})())
    state=main.build_graph().invoke({"trip":sample_trip(),"mode":"live","model":RejectingModel(),
                                     "revision_count":0,"revisions":[],"trace":[]},
                                    config={"recursion_limit":20})
    assert state["revision_count"]==2
    assert state["approved"] is False
    assert sum("Itinerary Writer received" in step for step in state["trace"])==3

def test_output_files_include_generated_content(tmp_path):
    state=run(sample_trip(),offline=True)
    md,js=save_outputs(state,tmp_path)
    assert md.exists() and js.exists()
    assert "OFFLINE SAMPLE DATA" in md.read_text(encoding="utf-8")
    saved=json.loads(js.read_text(encoding="utf-8"))
    assert saved["itinerary"]==state["itinerary"]

def test_trip_validation_rejects_invalid_party_and_duration():
    from main import validate_trip
    t=sample_trip(); t["travelers"]=0
    with pytest.raises(ValueError): validate_trip(t)
