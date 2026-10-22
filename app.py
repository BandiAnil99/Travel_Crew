"""Elegant, offline-first Streamlit interface for Travel Planner Crew."""
from datetime import date
import json
import streamlit as st

from main import run, sample_trip, save_outputs

st.set_page_config(page_title="Travel Planner Crew", page_icon="✦", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
:root { --ink:#18372f; --muted:#71817a; --green:#176b52; --mint:#eaf3ed; --line:#e2eae4; --paper:#fbfaf6; --gold:#c69b52; }
.stApp { background:var(--paper); color:var(--ink); font-family:'DM Sans',sans-serif; }
[data-testid="stHeader"] { background:rgba(251,250,246,.88); }
[data-testid="stSidebar"] { background:#f2f5ef; border-right:1px solid var(--line); }
[data-testid="stSidebar"] > div:first-child { padding-top:1.3rem; }
h1,h2,h3 { color:var(--ink); }
h1,h2 { font-family:'Playfair Display',serif !important; letter-spacing:-.025em; }
.hero { background:linear-gradient(115deg,#153e32 0%,#21644e 58%,#36745e 100%); border-radius:24px; padding:36px 42px; color:white; margin:4px 0 28px; position:relative; overflow:hidden; }
.hero:after { content:'✦'; position:absolute; right:7%; top:-55px; color:rgba(255,255,255,.08); font-size:220px; }
.hero-kicker { color:#c8ddce; text-transform:uppercase; font-size:11px; letter-spacing:.18em; font-weight:700; }
.hero-title { font:700 38px 'Playfair Display',serif; line-height:1.15; margin:12px 0 8px; }
.hero-copy { color:#e3eee6; font-size:15px; max-width:610px; line-height:1.6; }
.eyebrow { color:var(--green); text-transform:uppercase; letter-spacing:.14em; font-size:10px; font-weight:700; }
.section-title { font:600 25px 'Playfair Display',serif; color:var(--ink); margin:3px 0 14px; }
.metric { background:white; border:1px solid var(--line); border-radius:16px; padding:17px 19px; min-height:105px; box-shadow:0 4px 14px rgba(25,55,44,.035); }
.metric-label { color:var(--muted); text-transform:uppercase; letter-spacing:.1em; font-size:10px; font-weight:700; }
.metric-value { color:var(--ink); font-size:24px; font-weight:700; margin-top:8px; }
.metric-note { color:var(--muted); font-size:12px; margin-top:2px; }
.panel { background:white; border:1px solid var(--line); border-radius:18px; padding:22px 24px; margin:8px 0 16px; }
.welcome { border:1px dashed #cbd9ce; background:linear-gradient(140deg,#f3f7f1,#fff); border-radius:20px; padding:30px; }
.welcome-step { color:var(--muted); font-size:13px; padding:8px 0; }
.stButton > button[kind="primary"] { background:#176b52; border:0; border-radius:10px; font-weight:700; min-height:46px; }
.stButton > button[kind="primary"]:hover { background:#125740; border:0; }
.stDownloadButton > button { border-radius:10px; border-color:#cbd9ce; color:#176b52; }
div[data-testid="stProgress"] > div > div { background:#27845f; }
[data-testid="stMetric"] { background:white; border:1px solid var(--line); border-radius:14px; padding:14px 16px; }
[data-testid="stMetricLabel"] { color:var(--muted); }
button[data-baseweb="tab"] { font-weight:600; }
footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

defaults = sample_trip()

with st.sidebar:
    st.markdown("<div class='eyebrow'>Your journey</div><h2 style='font-size:25px;margin:5px 0 4px'>Trip details</h2><p style='color:#71817a;font-size:13px'>Shape a plan around your dates, pace, and budget.</p>", unsafe_allow_html=True)
    with st.form("trip_form"):
        destination = st.text_input("Where to?", defaults["destination"], placeholder="Jaipur, India")
        starting_city = st.text_input("Starting city", defaults["starting_city"])
        c1, c2 = st.columns(2)
        travelers = c1.number_input("Travelers", 1, 30, defaults["travelers"])
        days = c2.number_input("Days", 1, 31, defaults["days"])
        start_date = st.date_input("Start date", value=date.fromisoformat(defaults["start_date"]), min_value=date.today())
        c3, c4 = st.columns([2,1])
        budget = c3.number_input("Total budget", min_value=1.0, value=defaults["budget"], step=1000.0)
        currency = c4.selectbox("Currency", ["INR", "USD", "EUR", "GBP"])
        style = st.text_input("Travel style", defaults["style"])
        accommodation = st.text_input("Stay preference", defaults["accommodation"])
        transport = st.text_input("Getting around", defaults["transport"])
        requirements = st.text_area("Anything else?", defaults["requirements"], height=75)
        offline = st.toggle("Demo mode · no API key needed", value=True, help="Uses labeled example data and skips live search.")
        submit = st.form_submit_button("✦  Create my travel plan", type="primary", use_container_width=True)
    st.markdown("<div style='color:#71817a;font-size:11px;line-height:1.55;margin:12px 3px'>Live mode requires an OpenAI key in <code>.env</code>. Search uses Tavily when configured, otherwise Wikimedia.</div>", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="hero-kicker">Travel Planner Crew &nbsp;·&nbsp; Research, plan, refine</div>
  <div class="hero-title">A thoughtful trip,<br>planned together.</div>
  <div class="hero-copy">Four specialist agents work as one: finding the details, balancing your budget, shaping each day, and checking the plan before you go.</div>
</div>
""", unsafe_allow_html=True)

if submit:
    trip = {
        "destination": destination, "starting_city": starting_city,
        "travelers": int(travelers), "days": int(days), "start_date": start_date.isoformat(),
        "budget": float(budget), "currency": currency, "style": style,
        "accommodation": accommodation, "transport": transport, "requirements": requirements,
    }
    try:
        with st.spinner("Your researcher, budget analyst, itinerary writer, and critic are coordinating..."):
            result = run(trip, offline=offline)
            report_path, _ = save_outputs(result)
        st.session_state["crew_result"] = {key: value for key, value in result.items() if key != "model"}
        st.session_state["crew_report"] = report_path.read_text(encoding="utf-8")
    except Exception as exc:
        st.error(f"The plan could not be completed: {exc}")
        if not offline:
            st.info("Check OPENAI_API_KEY in .env. TAVILY_API_KEY is optional; Wikimedia is the fallback.")

result = st.session_state.get("crew_result")
if not result:
    st.markdown("<div class='eyebrow'>Start planning</div><div class='section-title'>Your next trip starts here</div>", unsafe_allow_html=True)
    left, right = st.columns([1.15, .85], gap="large")
    with left:
        st.markdown("<div class='welcome'><div style='font:600 23px Playfair Display;color:#18372f'>A little structure. A lot more room to enjoy.</div><p style='color:#71817a;line-height:1.65'>Set your destination and preferences in the trip panel. The crew will prepare a practical itinerary with a clear cost breakdown and a final quality review.</p><div class='welcome-step'>✦ &nbsp; Research grounded in search results</div><div class='welcome-step'>✦ &nbsp; Cost estimates checked with a calculator</div><div class='welcome-step'>✦ &nbsp; Critic feedback with bounded revisions</div></div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='panel'><div class='eyebrow'>Quick start</div><div class='section-title' style='font-size:21px'>Ready for a demo?</div><p style='color:#71817a;font-size:14px;line-height:1.6'>The sample trip is Jaipur for three days, departing from Hyderabad. Demo mode is selected by default, so no API key is needed.</p></div>", unsafe_allow_html=True)
else:
    trip = result["trip"]
    data = result.get("budget_data", {})
    code = trip.get("currency", "INR")
    symbol = {"INR":"₹", "USD":"$", "EUR":"€", "GBP":"£"}.get(code, code + " ")
    st.markdown(f"<div class='eyebrow'>Your trip snapshot</div><div class='section-title'>{trip.get('destination')} <span style='font:500 14px DM Sans;color:#71817a'>· {trip.get('days')} days · {trip.get('travelers')} travelers</span></div>", unsafe_allow_html=True)
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Estimated total", f"{symbol}{data.get('total',0):,.0f}", "Planning estimate")
    k2.metric("Per traveler", f"{symbol}{data.get('per_traveler',0):,.0f}", "Based on current assumptions")
    k3.metric("Budget remaining", f"{symbol}{data.get('remaining',0):,.0f}", "Negative means over budget")
    k4.metric("Plan review", "Approved" if result.get("approved") else "Needs attention", f"{result.get('revision_count',0)} revision(s)")
    cap = float(trip.get("budget", 0))
    if cap > 0:
        st.progress(min(max(float(data.get("total",0))/cap,0.0),1.0), text=f"Budget used · {data.get('total',0):,.0f} / {cap:,.0f} {code}")
    top_left, top_right = st.columns([1, 1])
    with top_left:
        st.caption(f"📍 {trip.get('starting_city')}  →  {trip.get('destination')}   ·   {trip.get('start_date')}")
    with top_right:
        st.download_button("↓  Download your plan", st.session_state["crew_report"], "travel_plan_output.md", "text/markdown", use_container_width=True)

    tab_plan, tab_budget, tab_research, tab_review = st.tabs(["✦  Itinerary", "◈  Budget", "⌕  Research", "✓  Critic review"])
    with tab_plan:
        st.markdown("<div class='panel'><div class='eyebrow'>Day by day</div>", unsafe_allow_html=True)
        st.markdown(result.get("itinerary", "No itinerary was returned."))
        st.markdown("</div>", unsafe_allow_html=True)
    with tab_budget:
        st.markdown("<div class='eyebrow'>Transparent estimates</div><div class='section-title'>Where the budget goes</div>", unsafe_allow_html=True)
        categories = data.get("categories", {})
        if categories:
            for label, amount in categories.items():
                a,b = st.columns([3,1]); a.write(label.replace("_"," ").title()); b.markdown(f"**{symbol}{amount:,.0f}**")
                st.progress(min(float(amount)/max(float(data.get("total",1)),1),1.0))
        st.caption("Costs are estimates rather than quotes. Verify fares, lodging availability, and attraction prices before booking.")
        with st.expander("Full budget calculation"):
            st.json(data)
    with tab_research:
        st.markdown("<div class='eyebrow'>Destination notes</div><div class='section-title'>Researcher's report</div>", unsafe_allow_html=True)
        st.markdown(result.get("research", "No research report was returned."))
        if result.get("mode") == "offline-demo":
            st.warning("Offline demo: these are labeled sample notes, not current web research.")
    with tab_review:
        st.markdown("<div class='eyebrow'>Quality check</div><div class='section-title'>The Critic's review</div>", unsafe_allow_html=True)
        try:
            review = json.loads(result.get("critique", "{}"))
            for issue in review.get("issues", []):
                st.markdown(f"- {issue}")
            if review.get("feedback"):
                st.info(review["feedback"])
            if review.get("limitations"):
                st.caption(review["limitations"])
        except (json.JSONDecodeError, TypeError):
            st.markdown(result.get("critique", "No review returned."))
        with st.expander("Agent handoff trace"):
            for item in result.get("trace", []):
                st.markdown(f"- {item}")
