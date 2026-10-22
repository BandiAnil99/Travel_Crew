"""Travel Planner Crew: four specialized agents coordinated by LangGraph."""
from __future__ import annotations
import argparse, json, os, math
from datetime import date, timedelta
from pathlib import Path
from typing import Any, TypedDict
from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from agents.prompts import AGENTS
from tools.calculator import calculate_trip_budget
from tools.web_search import search_travel_information

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"

class CrewState(TypedDict, total=False):
    trip: dict[str, Any]
    research: str
    budget: str
    budget_data: dict[str, Any]
    itinerary: str
    critique: str
    approved: bool
    revision_count: int
    revisions: list[str]
    trace: list[str]
    mode: str
    model: Any

def sample_trip() -> dict[str, Any]:
    start = date.today() + timedelta(days=30)
    return {"destination":"Jaipur, India", "starting_city":"Hyderabad, India", "travelers":2,
            "days":3, "start_date":start.isoformat(), "budget":30000.0, "currency":"INR",
            "style":"Culture, history, and local food", "accommodation":"Budget hotel",
            "transport":"Affordable public transportation and occasional taxis",
            "requirements":"Comfortable pace; verify current prices and hours before booking."}

def validate_trip(trip: dict[str, Any]) -> None:
    required = ("destination", "starting_city", "travelers", "days", "budget", "currency", "start_date")
    if any(not str(trip.get(k, "")).strip() for k in required):
        raise ValueError("Destination, starting city, dates, travelers, days, budget, and currency are required.")
    if int(trip["travelers"]) < 1 or not 1 <= int(trip["days"]) <= 31:
        raise ValueError("Travelers must be at least 1 and duration must be 1–31 days.")
    if not math.isfinite(float(trip["budget"])) or float(trip["budget"]) <= 0: raise ValueError("Budget must be a finite amount greater than zero.")
    if trip["currency"].upper() not in {"INR", "USD", "EUR", "GBP"}: raise ValueError("Currency must be INR, USD, EUR, or GBP.")
    if date.fromisoformat(trip["start_date"]) < date.today(): raise ValueError("Travel date cannot be in the past.")

def _call_model(s: CrewState, agent: str, context: str) -> str:
    spec = AGENTS[agent]
    prompt = (f"Role: {spec['role']}\nGoal: {spec['goal']}\nBackstory: {spec['backstory']}\n"
              f"Trip requirements: {json.dumps(s['trip'], ensure_ascii=False)}\n\nUpstream context:\n{context}\n\n{spec['system']}")
    return str(s["model"].invoke(prompt).content).strip()

def build_graph():
    """StateGraph edges explicitly pass outputs; critic can request at most two revisions."""
    def researcher(s: CrewState) -> dict:
        if s["mode"] == "offline-demo":
            research = ("OFFLINE SAMPLE DATA — not live research: Jaipur is known for its historic walled city, Hawa Mahal, "
                        "Amber Fort, and regional cuisine. These are planning suggestions; current hours, access, weather, "
                        "transport and prices were not checked. No live sources were retrieved.")
            call = "Search skipped in offline demo; no live facts or URLs claimed."
        else:
            result = search_travel_information.invoke({"query":f"{s['trip']['destination']} attractions local transport official visitor information"})
            call = f"Destination researcher called search_travel_information; status={result['status']}; provider={result.get('provider', 'unavailable')}"
            research = _call_model(s, "researcher", json.dumps(result, ensure_ascii=False))
        return {"research":research, "trace":s.get("trace",[]) + [call, "Link A: research report passed to Budget Analyst."]}

    def budgeter(s: CrewState) -> dict:
        n,d=int(s['trip']['travelers']),int(s['trip']['days']); cur=s['trip']['currency'].upper()
        daily={"INR":(1800,1300,1200,900,500),"USD":(35,45,25,25,15),"EUR":(32,42,24,23,14),"GBP":(28,38,22,20,12)}
        rates=daily.get(cur,daily['INR'])
        cats=[rates[0]*n,rates[1]*max(d-1,0)*n,rates[2]*d*n,rates[3]*d*n,rates[4]*d*n]
        keys=("transportation","accommodation","meals","attractions","miscellaneous")
        calc=calculate_trip_budget.invoke(dict(zip(keys,cats)) | {"travelers":n,"budget":float(s['trip']['budget'])})
        if s['mode']=="offline-demo":
            budget="Illustrative estimates, not current prices. Intercity fare is a placeholder and must be verified.\n"+json.dumps(calc,indent=2)
        else: budget=_call_model(s,"budget",f"Research: {s['research']}\nCalculator result: {json.dumps(calc)}")
        return {"budget":budget,"budget_data":calc,"trace":s['trace']+["Budget Analyst called calculate_trip_budget with validated numeric categories.","Link B: research and calculator-backed budget passed to Itinerary Writer."]}

    def writer(s: CrewState) -> dict:
        feedback=s.get("critique","No critic feedback yet.")
        revising=bool(s.get("critique")) and not s.get("approved",False)
        revision_number=s.get("revision_count",0)+(1 if revising else 0)
        context=f"Research: {s['research']}\nBudget: {s['budget']}\nCritic feedback: {feedback}"
        if s['mode']=="offline-demo":
            t=s['trip']; itinerary=(f"Day 1 ({t['start_date']}): Morning arrival/check-in and rest; afternoon historic center and Hawa Mahal area; evening Rajasthani dinner.\n\n"
              "Day 2: Morning Amber Fort (confirm access/hours); afternoon meal, return transfer and rest; evening flexible local market visit if open.\n\n"
              "Day 3: Morning City Palace area (confirm tickets/hours); afternoon lunch and flexible neighborhood time; evening departure transfer.\n\n"
              f"Estimated total: {s['budget_data']['total']:.2f} {t['currency']} for {t['travelers']}; estimated daily spending: "
              f"{s['budget_data']['total']/max(int(t['days']),1):.2f} {t['currency']} per day for the group, averaged across the trip.")
            if revising: itinerary+="\nRevision: added transfer/rest buffers and explicit fare and opening-hour verification."
        else: itinerary=_call_model(s,"writer",context)
        return {"itinerary":itinerary,"revision_count":revision_number,"trace":s['trace']+[f"Itinerary Writer received research + budget + feedback (revision {revision_number}).","Link C: itinerary and costs passed to Critic."]}

    def critic(s: CrewState) -> dict:
        context=f"Research: {s['research']}\nBudget: {s['budget']}\nItinerary: {s['itinerary']}\nBudget numbers: {json.dumps(s.get('budget_data',{}))}"
        if s['mode']=="offline-demo":
            issues=["Opening hours and ticket prices are unverified.","Origin-to-destination fare is an estimate.","Traffic and live availability are unknown."]
            approved=s.get('revision_count',0)>=1
            critique=json.dumps({"approved":approved,"issues":issues,"feedback":"Add transfer/rest buffers and verify attraction schedules and actual fares before booking.","limitations":"Offline sample data; not live research."},indent=2)
        else:
            critique=_call_model(s,"critic",context)
            approved='"approved": true' in critique.lower() or "approved: true" in critique.lower()
        count=s.get('revision_count',0)
        revisions=s.get('revisions',[])
        if not approved and count<2: revisions=revisions+[critique]
        return {"critique":critique,"approved":approved,"revision_count":count,"revisions":revisions,"trace":s['trace']+[f"Critic evaluated the actual itinerary; approved={approved}."]}

    g=StateGraph(CrewState)
    for name,node in (("researcher",researcher),("budgeter",budgeter),("writer",writer),("critic",critic)): g.add_node(name,node)
    g.add_edge(START,"researcher"); g.add_edge("researcher","budgeter"); g.add_edge("budgeter","writer"); g.add_edge("writer","critic")
    g.add_conditional_edges("critic",lambda s:"writer" if not s['approved'] and s['revision_count']<2 else END,{"writer":"writer",END:END})
    return g.compile()

def render_report(s: CrewState) -> str:
    t=s['trip']; b=s.get('budget_data',{})
    return f"""# Travel Planner Crew — {t['destination']}\n\n## Trip overview and requirements\n- Starting city: {t['starting_city']} | Dates: {t['start_date']} for {t['days']} days\n- Travelers: {t['travelers']} | Budget: {t['budget']} {t['currency']}\n- Style: {t.get('style','')} | Accommodation: {t.get('accommodation','')} | Transport: {t.get('transport','')}\n- Special requirements: {t.get('requirements','')}\n\n## Destination Researcher report\n{ s['research'] }\n\n## Important attractions and travel considerations\n{ s['research'] }\n\n## Budget Analyst report and categorized estimated expenses\n{s['budget']}\n\n## Total cost and cost per traveler\n- Total: {b.get('total','See report')} {t['currency']}\n- Per traveler: {b.get('per_traveler','See report')} {t['currency']}\n\n## Budget comparison and suggested savings\nRemaining against budget: {b.get('remaining','See report')} {t['currency']} (negative means over). Prefer free attractions, local transport, and lower-cost lodging if needed.\n\n## Day-by-day itinerary and daily estimated spending\n{s['itinerary']}\n\n## Critic's findings\n{s['critique']}\n\n## Revisions made in response to feedback\n{chr(10).join('- '+x for x in s.get('revisions',[])) or 'No revision requested.'}\n\n## Final approval status\n{'APPROVED' if s.get('approved') else 'NOT APPROVED — limitations remain'} after {s.get('revision_count',0)} revision cycle(s).\n\n## Sources and URLs\n{'No live sources; offline demonstration data is illustrative.' if s.get('mode')=='offline-demo' else 'See URLs returned in the research report; no citations are invented.'}\n\n## Assumptions, limitations, and warnings\nPrices and availability vary by date. Expenses are estimates, not quotes. Verify transport fares, lodging availability, attraction hours, entry rules, and weather before booking. Offline mode does not search the web.\n\n## Sample execution trace\n{chr(10).join('- '+x for x in s.get('trace',[]))}\n"""

def save_outputs(s: CrewState, output_dir: Path=OUT) -> tuple[Path,Path]:
    output_dir.mkdir(parents=True,exist_ok=True); md=output_dir/'travel_plan_output.md'; js=output_dir/'agent_state.json'
    md.write_text(render_report(s),encoding='utf-8')
    js.write_text(json.dumps({k:v for k,v in s.items() if k!='model'},ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    trace=("# Sample execution trace\n\n"+"\n".join("- "+x for x in s.get('trace',[]))+
          "\n\n## Search-tool check\n\nThe automated empty-results test invoked the LangChain search tool with a mocked empty service response. This verified graceful handling only; it was not a live web search. The offline planning run above skipped live search because no API credentials were configured.\n")
    (output_dir/'sample_execution_trace.md').write_text(trace,encoding='utf-8')
    return md,js

def run(trip: dict[str,Any], offline: bool=False) -> CrewState:
    validate_trip(trip); load_dotenv(ROOT/'.env'); model=None
    mode='offline-demo' if offline else 'live'
    if not offline:
        if not os.getenv('OPENAI_API_KEY'): raise RuntimeError("OPENAI_API_KEY is missing. Configure .env or run --offline-demo.")
        from langchain_openai import ChatOpenAI
        model=ChatOpenAI(model=os.getenv('OPENAI_MODEL','gpt-4o-mini'),temperature=0.2)
    return build_graph().invoke({"trip":trip,"mode":mode,"model":model,"revision_count":0,"revisions":[],"trace":[f"Execution mode: {mode}."]},config={"recursion_limit":20})

def main() -> None:
    p=argparse.ArgumentParser(description="Four-agent LangGraph travel planner")
    p.add_argument('--offline-demo',action='store_true',help='Use labeled sample information without live APIs')
    for flag,typ in (('--destination',str),('--starting-city',str),('--travelers',int),('--days',int),('--budget',float),('--start-date',str),('--currency',str),('--style',str),('--accommodation',str),('--transport',str),('--requirements',str)): p.add_argument(flag,type=typ)
    a=p.parse_args(); trip=sample_trip()
    for arg,key in ((a.destination,'destination'),(a.starting_city,'starting_city'),(a.travelers,'travelers'),(a.days,'days'),(a.budget,'budget'),(a.start_date,'start_date'),(a.currency,'currency'),(a.style,'style'),(a.accommodation,'accommodation'),(a.transport,'transport'),(a.requirements,'requirements')):
        if arg is not None: trip[key]=arg
    state=run(trip,a.offline_demo); md,js=save_outputs(state)
    print(f"Plan complete ({state['mode']}). Markdown: {md}\nAgent state: {js}")

if __name__=='__main__': main()
