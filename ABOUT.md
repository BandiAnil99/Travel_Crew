# About Travel Planner Crew

Travel Planner Crew is a Python travel-planning assignment built with LangChain tools and LangGraph. Four focused agents collaborate through a shared workflow to research a destination, estimate a trip budget, write a day-by-day plan, and review it for problems. The Critic can request up to two itinerary revisions.

## Agents

1. **Destination Researcher** searches for attractions and travel information and reports source links and uncertainty.
2. **Budget Analyst** calls the calculator tool to total estimated costs, calculate per-traveler cost, and compare the estimate with the budget.
3. **Itinerary Writer** uses the research, budget, dates, and traveler preferences to build the schedule.
4. **Critic** checks the plan's costs, logistics, evidence, and fit with the request, then approves it or sends feedback for revision.

## Tools and workflow

- `search_travel_information` is a LangChain tool. It uses Tavily when configured; otherwise it uses Wikimedia search.
- `calculate_trip_budget` is a LangChain tool that validates expenses and calculates totals and budget remaining.
- LangGraph passes each agent's output to the next agent and routes Critic feedback back to the Itinerary Writer within a two-revision limit.

## Setup and run

Install dependencies with `python -m pip install -r requirements.txt`. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`; `TAVILY_API_KEY` is optional. Keep `.env` private.

Launch the browser interface with `streamlit run app.py`. Run the live CLI workflow with `python main.py`, or without credentials using `python main.py --offline-demo`; offline mode labels its sample information and does not perform live search. Run checks with `python -m pytest`.

Generated reports are saved to `outputs/travel_plan_output.md`, `outputs/agent_state.json`, and `outputs/sample_execution_trace.md`. Costs in the plan are estimates and should be checked against current prices and availability before booking.
