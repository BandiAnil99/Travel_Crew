# Travel Planner Crew

A Python 3.10+ travel planner with four distinct agents coordinated by a LangGraph state graph. Each node receives explicit structured state from the previous task, and the Critic can send feedback through a bounded itinerary revision loop.

## Agents and tools

- **Destination Researcher** focuses on sourced attractions, culture, transport and uncertainty. Its LangChain `search_travel_information` tool uses Tavily when `TAVILY_API_KEY` is set, and otherwise the project's Wikimedia search integration.
- **Budget Analyst** uses the LangChain `calculate_trip_budget` tool for validated arithmetic, totals, per-person cost and budget comparison. Example costs are estimates, not live quotes.
- **Itinerary Writer** uses research and budget outputs plus traveler preferences to schedule each day.
- **Critic** reviews that itinerary, budget, sources and requirements. Feedback loops to the Writer at most twice; residual limitations are reported.

The LangGraph dependency chain is `START → Researcher → Budget Analyst → Itinerary Writer → Critic`. Critic conditionally returns to Writer until approval or two revisions. Shared `CrewState` contains the trip request and each agent's output. The tool calls are explicit in the workflow, so both search (live mode) and calculator are invoked, not merely mentioned in prompts.

## Install and run

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`, then set `OPENAI_API_KEY`. `OPENAI_MODEL` defaults to `gpt-4o-mini`; choose a model available to your account. Set `TAVILY_API_KEY` to use Tavily. Without it, search uses Wikimedia. Keep `.env` private; it is ignored by git.

Launch the browser interface with `streamlit run app.py`. It starts in offline demo mode by default; turn off that option to use live mode after configuring the OpenAI key.

```bash
python main.py
```

The default sample is a three-day Jaipur trip from Hyderabad for two travelers, INR 30,000, with culture/history/food preferences and dates 30 days in the future. Customize in the browser form or with `--destination`, `--starting-city`, `--travelers`, `--days`, `--start-date`, `--budget`, `--currency`, `--style`, `--accommodation`, `--transport`, and `--requirements` in CLI mode.

If no API keys are available, run `python main.py --offline-demo`. That mode makes no search or LLM calls. Its sample facts and costs are labeled as illustrative, and it does not claim live research. Both modes automatically write `outputs/travel_plan_output.md`, `outputs/agent_state.json`, and `outputs/sample_execution_trace.md`.

## Tests

```bash
pytest
```

Tests cover calculator arithmetic and invalid values, empty search results, graph context and Critic revision behavior, and output creation. Run the offline demo to see a reproducible complete trace.

## Limitations

There is no booking inventory integration. Prices, fares, schedules and availability are not live quotes. Search snippets can be incomplete, and the itinerary should be checked against official attraction pages and current transport schedules. The live run requires an OpenAI key and internet access; a Tavily key is optional. Offline demo mode must never be described as live research.


<img width="1920" height="1080" alt="Screenshot (381)" src="https://github.com/user-attachments/assets/be1948fd-530c-447f-9183-ad0ada58eec4" />


