"""Braylliant AI — Phase 2: Gemini Chat + Free-first Project Scout.

Deploy on Streamlit Community Cloud. Set GEMINI_API_KEY in App settings > Secrets.
Public search snippets are discovery signals, NOT verified open contracts.
"""

import csv
import io
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import streamlit as st
from ddgs import DDGS
from google import genai

st.set_page_config(page_title="Braylliant AI | Project Scout", page_icon="🔎", layout="wide")

SERVICES = {
    "AI data annotation": '"data annotation" outsourcing vendor AI',
    "Video / computer vision": '"video annotation" computer vision outsourcing partner',
    "Speech / voice collection": '"speech data collection" vendor partner',
    "Transcription": '"transcription" multilingual outsourcing vendor',
    "Translation / localization": '"localization" "language data" vendor AI',
    "LLM / GenAI evaluation": '"LLM evaluation" "human evaluation" vendor',
    "RLHF / HITL / QA": '"RLHF" "human in the loop" services partner',
    "Participant recruitment": '"participant recruitment" "data collection" research vendor',
}
REGIONS = {
    "USA": "United States", "UK": "United Kingdom", "Canada": "Canada",
    "Europe": "Europe", "Australia": "Australia", "Singapore": "Singapore",
    "UAE": "United Arab Emirates", "Global": "global international",
}
SYSTEM = """You are Braylliant AI, a careful business-development assistant for
Braylliant IT Solutions Private Limited, an India-based managed AI data services provider.
Capabilities include annotation, computer vision, speech collection, transcription,
localization, LLM evaluation, RLHF, HITL, QA and participant recruitment.
Distinguish verified facts from speculation. Never invent contracts, contacts, links,
customer relationships, company performance, or eligibility. Do not claim live web
access in chat unless actual search evidence has been supplied. Recommend practical,
free-first approaches and seek direct foreign clients or prime contractors."""


def api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        key = ""
    return key or os.getenv("GEMINI_API_KEY", "")


def generate(prompt, model):
    client = genai.Client(api_key=api_key())
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text or "The model returned no text. Please try again."
    finally:
        client.close()


def clean_url(value):
    url = (value or "").strip()
    parsed = urlparse(url)
    return url if parsed.scheme in ("https", "http") and parsed.netloc else ""


def search_web(query, limit):
    with DDGS(timeout=20) as ddgs:
        return list(ddgs.text(query, max_results=limit))


def build_queries(services, regions, custom):
    if custom.strip():
        return [custom.strip()]
    # Cap searches to avoid exhausting free, rate-limited search backends.
    queries = []
    for service in services:
        for region in regions:
            phrase = SERVICES[service]
            geography = REGIONS[region]
            queries.append(f'{phrase} {geography} (RFP OR tender OR "vendor" OR "partner" OR "supplier")')
    return queries[:12]


def scout(queries, per_query):
    leads = []
    seen = set()
    errors = []
    for query in queries:
        try:
            results = search_web(query, per_query)
            for item in results:
                url = clean_url(item.get("href") or item.get("url"))
                if not url:
                    continue
                canonical = url.split("#", 1)[0].rstrip("/").lower()
                if canonical in seen:
                    continue
                seen.add(canonical)
                leads.append({
                    "title": str(item.get("title") or "Untitled")[:300],
                    "url": url,
                    "snippet": str(item.get("body") or item.get("snippet") or "")[:1400],
                    "query": query,
                    "found_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                    "status": "Unverified discovery — review source page",
                })
        except Exception as exc:
            errors.append(f"Search failed for '{query[:75]}': {exc}")
    return leads, errors


def csv_bytes(rows):
    output = io.StringIO()
    columns = ["title", "url", "snippet", "query", "found_utc", "status"]
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


st.title("🔎 Braylliant AI")
st.caption("Phase 2 · Gemini assistant + free-first international Project Scout")
key = api_key()
with st.sidebar:
    st.subheader("Configuration")
    model = st.text_input("Gemini model", value="gemini-3.8-flash", help="Change if this model is not available to your API key.")
    if key:
        st.success("Gemini API key found in secrets/environment")
    else:
        st.warning("Add GEMINI_API_KEY in Streamlit App settings → Secrets to use Gemini features.")
    st.caption("Free public search can be incomplete or rate-limited. Gemini API quotas and pricing depend on your Google account.")

chat_tab, scout_tab = st.tabs(["💬 Gemini Chat", "🌍 Live Project Scout"])

with chat_tab:
    st.subheader("Business development assistant")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("Ask about prospects, outreach, service pitches, or project planning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            if not key:
                answer = "Please configure GEMINI_API_KEY in Streamlit Secrets first."
            else:
                history = "\n".join(f'{m["role"]}: {m["content"][:2500]}' for m in st.session_state.messages[-12:])
                try:
                    answer = generate(f"{SYSTEM}\n\nConversation:\n{history}\nassistant:", model)
                except Exception as exc:
                    answer = f"Gemini request failed: {exc}. Check the API key, model name and quota."
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

with scout_tab:
    st.subheader("Find international AI data outsourcing leads")
    st.info("Results are public search snippets, not verified active RFPs. Open each source, confirm its date and supplier eligibility, and review before outreach.")
    left, right = st.columns(2)
    with left:
        selected_services = st.multiselect("Service categories", list(SERVICES), default=["AI data annotation", "Speech / voice collection", "LLM / GenAI evaluation"])
    with right:
        selected_regions = st.multiselect("Target markets", list(REGIONS), default=["USA", "UK", "Europe"])
    custom_query = st.text_input("Optional exact company name, website, or custom search phrase", placeholder="e.g. example.com AI data supplier RFP")
    per_query = st.slider("Results per search", min_value=2, max_value=10, value=5)
    st.caption("Up to 12 searches per click. No paid lead databases or automatic contacting.")
    if st.button("Search public web", type="primary"):
        if not custom_query.strip() and (not selected_services or not selected_regions):
            st.error("Choose at least one service and one market, or enter a custom search phrase.")
        else:
            queries = build_queries(selected_services, selected_regions, custom_query)
            with st.spinner(f"Searching {len(queries)} public queries..."):
                leads, errors = scout(queries, per_query)
            st.session_state["leads"] = leads
            st.session_state["search_errors"] = errors
            st.session_state.pop("analysis", None)
    leads = st.session_state.get("leads", [])
    for error in st.session_state.get("search_errors", []):
        st.warning(error)
    if leads:
        st.success(f"{len(leads)} unique public search results found. None have been independently verified.")
        st.download_button("Download leads as CSV (opens in Excel)", data=csv_bytes(leads), file_name="braylliant_project_scout_leads.csv", mime="text/csv")
        for index, lead in enumerate(leads, 1):
            with st.expander(f'{index}. {lead["title"]}', expanded=index <= 3):
                st.markdown(f'**Source:** [{lead["url"]}]({lead["url"]})')
                st.write(lead["snippet"] or "No snippet supplied by the search engine.")
                st.caption(f'Search: {lead["query"]} · Found: {lead["found_utc"]} · {lead["status"]}')
        if st.button("Analyze these leads with Gemini"):
            if not key:
                st.error("Add GEMINI_API_KEY in Streamlit Secrets first.")
            else:
                excerpts = "\n\n".join(
                    f'{i}. Title: {x["title"]}\nURL: {x["url"]}\nSnippet: {x["snippet"]}'
                    for i, x in enumerate(leads[:25], 1)
                )
                instruction = """Analyze these SEARCH RESULT SNIPPETS only for Braylliant's India-based AI data services.
Do not claim to have visited pages or verified any open opportunities. Do not invent
publication dates, procurement status, buyer contacts, budgets or eligibility.
For each promising item, label either 'Potential active opportunity — needs source-page
verification' ONLY if the snippet explicitly mentions an open/current requirement,
or 'Potential client prospect — outreach required'. Rank up to 10 by fit; give
source URLs, evidence from the snippet, uncertainty, and a suggested next verification
step. Prioritize direct end clients and prime contractors, recurring work, and feasible
paid pilots with a 100–200-person deployable team. Note that staffing is contingent
on confirmed requirements. Clearly state if no convincing lead was found."""
                with st.spinner("Gemini is reviewing search snippets..."):
                    try:
                        st.session_state["analysis"] = generate(f"{SYSTEM}\n\n{instruction}\n\n{excerpts}", model)
                    except Exception as exc:
                        st.error(f"Analysis failed: {exc}")
        if st.session_state.get("analysis"):
            st.markdown("### Gemini lead assessment")
            st.markdown(st.session_state["analysis"])
    elif "leads" in st.session_state:
        st.warning("No results returned. Try fewer searches or a more specific query; free search providers may rate-limit requests.")

st.divider()
st.caption("Phase 2 is manual and session-based. Daily monitoring, persistent Excel CRM updates and notifications are future phases; this app does not perform them automatically.")
