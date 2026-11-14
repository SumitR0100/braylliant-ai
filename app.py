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


# Search snippets are untrusted discovery signals, not verified procurement notices.
BLOCKED_DOMAINS = {"icloud.com", "apple.com", "youtube.com", "facebook.com", "instagram.com", "pinterest.com", "tiktok.com"}
SERVICE_TERMS = (
    "annotation", "annotat", "labeling", "labelling", "training data", "data collection",
    "speech data", "voice data", "audio data", "transcription", "transcrib",
    "translation", "localization", "localisation", "multilingual", "computer vision",
    "video data", "image data", "llm evaluation", "model evaluation", "rlhf",
    "human feedback", "human-in-the-loop", "human in the loop", "ai dataset",
    "dataset creation", "data quality", "content moderation", "participant recruitment",
)
BUYER_TERMS = (
    "rfp", "request for proposal", "tender", "procurement", "request for quotation",
    "supplier", "vendor", "subcontract", "outsourc", "service provider",
    "partner", "bid", "contract", "expression of interest", "sourcing",
)
ACTIVE_TERMS = ("open rfp", "invitation to bid", "seeking vendors", "looking for vendors", "request for proposals", "supplier registration", "call for proposals")


def make_short_queries(services, regions, custom):
    custom = custom.strip()
    # Search engines accept keyword queries, not ChatGPT-style paragraphs.
    # A company name or URL is useful as a targeted lookup.
    if custom and len(custom.split()) <= 12 and len(custom) <= 120:
        target = custom
        if target.startswith(("https://", "http://")):
            target = urlparse(target).netloc.removeprefix("www.")
        if "." in target and " " not in target:
            return [f'site:{target} (supplier OR procurement OR vendor OR "data annotation")',
                    f'"{target}" "AI data" (vendor OR partner OR outsourcing)']
        return [f'{target} AI data annotation supplier vendor',
                f'{target} AI data collection outsourcing partnership']
    # Longer text is treated as an instruction, not submitted verbatim.
    chosen_services = services or list(SERVICES)[:3]
    chosen_regions = regions or ["Global"]
    queries = []
    for service in chosen_services:
        core = SERVICES[service].replace(' outsourcing vendor AI', '').replace(' outsourcing partner', '').replace(' vendor partner', '').replace(' outsourcing vendor', '').replace(' vendor', '').replace(' services partner', '').replace(' research vendor', '')
        for region in chosen_regions:
            geo = REGIONS[region]
            queries.append(f'{core} {geo} "request for proposal" OR "seeking vendors"')
            queries.append(f'{core} {geo} "outsourcing" "supplier"')
    # Remove duplicates and limit free-search usage.
    return list(dict.fromkeys(queries))[:12]


def relevance(item):
    title = str(item.get("title") or "")
    snippet = str(item.get("body") or item.get("snippet") or "")
    url = clean_url(item.get("href") or item.get("url"))
    if not url:
        return None
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    if any(host == d or host.endswith("." + d) for d in BLOCKED_DOMAINS):
        return None
    text = (title + " " + snippet).lower()
    service_hits = sum(term in text for term in SERVICE_TERMS)
    buyer_hits = sum(term in text for term in BUYER_TERMS)
    if service_hits == 0 or buyer_hits == 0:
        return None
    # Ranking is heuristic; it does NOT verify whether a contract is currently open.
    score = min(10, 2 + min(service_hits, 3) + min(buyer_hits, 3) + (2 if any(t in text for t in ACTIVE_TERMS) else 0))
    status = "Possible procurement signal — verify source" if any(t in text for t in ACTIVE_TERMS) else "Potential client/prospect — verify source"
    return {"title": title[:300] or "Untitled", "url": url,
            "snippet": snippet[:1400], "score": score, "status": status}


def scout(queries, per_query):
    leads, errors, seen = [], [], set()
    discarded = 0
    for query in queries:
        try:
            for item in search_web(query, per_query):
                lead = relevance(item)
                if lead is None:
                    discarded += 1
                    continue
                canonical = lead["url"].split("#", 1)[0].rstrip("/").lower()
                if canonical in seen:
                    continue
                seen.add(canonical)
                lead.update({"query": query,
                             "found_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")})
                leads.append(lead)
        except Exception as exc:
            errors.append(f"Search failed for '{query[:75]}': {exc}")
    leads.sort(key=lambda x: x["score"], reverse=True)
    return leads, errors, discarded


def csv_bytes(rows):
    output = io.StringIO()
    columns = ["title", "url", "snippet", "score", "query", "found_utc", "status"]
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
    st.caption("Up to 12 targeted searches per click. Long instructions are converted to short keyword searches. Scores are heuristic, not proof of an open project.")
    if st.button("Search public web", type="primary"):
        if not custom_query.strip() and (not selected_services or not selected_regions):
            st.error("Choose at least one service and one market, or enter a custom search phrase.")
        else:
            queries = make_short_queries(selected_services, selected_regions, custom_query)
            with st.spinner(f"Searching {len(queries)} public queries..."):
                leads, errors, discarded = scout(queries, per_query)
            st.session_state["leads"] = leads
            st.session_state["search_errors"] = errors
            st.session_state["discarded"] = discarded
            st.session_state["queries_used"] = queries
            st.session_state.pop("analysis", None)
    leads = st.session_state.get("leads", [])
    for error in st.session_state.get("search_errors", []):
        st.warning(error)
    if leads:
        st.success(f"{len(leads)} potentially relevant public results found; {st.session_state.get('discarded', 0)} unrelated results filtered out. None independently verified.")
        st.download_button("Download leads as CSV (opens in Excel)", data=csv_bytes(leads), file_name="braylliant_project_scout_leads.csv", mime="text/csv")
        for index, lead in enumerate(leads, 1):
            with st.expander(f'{index}. [Fit {lead["score"]}/10] {lead["title"]}', expanded=index <= 3):
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
        st.warning("No relevant results passed the basic filters. This does not mean no opportunities exist. Try a different service, market or shorter company-specific query.")

st.divider()
st.caption("Phase 2 is manual and session-based. Daily monitoring, persistent Excel CRM updates and notifications are future phases; this app does not perform them automatically.")
