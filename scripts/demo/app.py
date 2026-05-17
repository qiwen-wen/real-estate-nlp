"""Real Estate Intelligent Search — Week 11 Streamlit demo.

Run locally:
    # terminal 1
    uvicorn scripts.api.main:app --reload --port 8000
    # terminal 2
    streamlit run scripts/demo/app.py

Point at a hosted backend:
    API_BASE_URL=https://idx-nlp-api.onrender.com streamlit run scripts/demo/app.py
"""

import os
import sys
from datetime import datetime, timezone

# `streamlit run` invokes this file as a top-level script, so the project root
# isn't on sys.path. Add it before any `scripts.*` import.
_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _BASE not in sys.path:
    sys.path.append(_BASE)

import streamlit as st

from scripts.demo import api_client as api
from scripts.demo import metrics_log

st.set_page_config(
    page_title="Real Estate Intelligent Search",
    layout="wide",
)

EXAMPLE_QUERIES = [
    "3 bed 2 bath under 700k in Irvine",
    "cozy starter home with a big yard",
    "modern kitchen with granite countertops and pool",
    "what makes Anaheim a good place to buy?",
    "luxury home with mountain view and updated bathrooms",
]

INTENT_LABELS = {
    "ready_to_buy": "Ready to buy — filter & search",
    "researching": "Researching — informational",
    "browsing": "Browsing — exploratory",
}

# ── Session state ────────────────────────────────────────────────────────────
if "query" not in st.session_state:
    st.session_state.query = EXAMPLE_QUERIES[0]
if "last_search" not in st.session_state:
    # Persisted search payload — survives reruns triggered by thumb clicks
    # so we don't have to re-call the API every interaction.
    st.session_state.last_search = None


def _set_query(value: str) -> None:
    # Must mutate session_state inside a callback — Streamlit forbids writes
    # to a widget-bound key after the widget has been instantiated this run.
    st.session_state.query = value
    # Old results would be misleading next to a brand-new query.
    st.session_state.last_search = None


def _rate_search(value: str) -> None:
    state = st.session_state.last_search
    if not state or state.get("rating"):
        return
    state["rating"] = value
    metrics_log.append_rating({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": state["query"],
        "search_timestamp": state["submitted_at"],
        "rating": value,
    })


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    top_k = st.slider("Number of results", min_value=1, max_value=20, value=5)
    summarize_results = st.checkbox("Generate listing summaries", value=True)
    show_compliance = st.checkbox("Run Fair Housing check on results", value=True)

    st.divider()
    st.subheader("API status")
    try:
        h, _ = api.health()
        if h["status"] == "ok":
            st.success(f"API: {h['status']}")
        else:
            st.warning(f"API: {h['status']}")
        with st.expander("Components"):
            st.json(h["components"])
    except api.APIError as exc:
        st.error(f"API unreachable\n\n{exc}")
        st.caption(f"Base URL: `{api.API_BASE_URL}`")

    st.divider()
    st.page_link("pages/1_metrics.py", label="Open metrics dashboard")

# ── Header ───────────────────────────────────────────────────────────────────
st.title("Real Estate Intelligent Search")
st.caption(
    "Natural-language search over MLS listings — intent classification, "
    "filter extraction, semantic retrieval, summarization, and Fair Housing compliance."
)

# ── Shared query input ───────────────────────────────────────────────────────
with st.form("search_form", clear_on_submit=False):
    col1, col2 = st.columns([5, 1])
    with col1:
        st.text_input(
            "What are you looking for?",
            key="query",
            placeholder="e.g. 3 bed 2 bath under 700k in Irvine",
            label_visibility="collapsed",
        )
    with col2:
        submitted = st.form_submit_button("Search", type="primary", use_container_width=True)

st.caption("Try one of these:")
ex_cols = st.columns(len(EXAMPLE_QUERIES))
for col, ex in zip(ex_cols, EXAMPLE_QUERIES):
    col.button(
        ex,
        key=f"ex_{hash(ex)}",
        use_container_width=True,
        on_click=_set_query,
        args=(ex,),
    )

query = st.session_state.query.strip()

# ── Submission: run pipeline, persist to state, log to JSONL ─────────────────
if submitted and query:
    with st.spinner("Running NLP pipeline (parse + semantic + keyword in parallel)..."):
        try:
            parsed, parse_ms = api.parse_query(query)
        except api.APIError as exc:
            st.error(f"parse-query failed: {exc}")
            st.stop()

        both = api.search_both(query, top_k=top_k)

    sem = both["semantic"]
    kw = both["keyword"]
    sem_json = sem[0] if not isinstance(sem, api.APIError) else None
    sem_ms = sem[1] if not isinstance(sem, api.APIError) else None
    kw_json = kw[0] if not isinstance(kw, api.APIError) else None
    kw_ms = kw[1] if not isinstance(kw, api.APIError) else None

    submitted_at = datetime.now(timezone.utc).isoformat()
    st.session_state.last_search = {
        "query": query,
        "top_k": top_k,
        "submitted_at": submitted_at,
        "parsed": parsed,
        "parse_ms": parse_ms,
        "semantic_json": sem_json,
        "semantic_error": str(sem) if isinstance(sem, api.APIError) else None,
        "semantic_ms": sem_ms,
        "keyword_json": kw_json,
        "keyword_error": str(kw) if isinstance(kw, api.APIError) else None,
        "keyword_ms": kw_ms,
        "rating": None,
    }

    metrics_log.append_search({
        "timestamp": submitted_at,
        "query": query,
        "intent": parsed["intent"],
        "confidence": parsed["confidence"],
        "sql_ready": parsed["sql_ready"],
        "filters": parsed.get("filters") or {},
        "top_k": top_k,
        "result_count": sem_json["count"] if sem_json else 0,
        "parse_ms": parse_ms,
        "semantic_ms": sem_ms,
        "keyword_ms": kw_ms,
    })

state = st.session_state.last_search

# ── Per-search rating banner ─────────────────────────────────────────────────
if state:
    bar1, bar2, bar3 = st.columns([6, 1, 1])
    rating = state.get("rating")
    if rating:
        bar1.caption(f"_Rated **{'helpful' if rating == 'up' else 'not useful'}** — thanks._")
    else:
        bar1.caption("_Rate these results to help improve the demo:_")
    bar2.button(
        "Helpful",
        on_click=_rate_search,
        args=("up",),
        use_container_width=True,
        disabled=rating is not None,
        type="primary" if rating == "up" else "secondary",
    )
    bar3.button(
        "Not useful",
        on_click=_rate_search,
        args=("down",),
        use_container_width=True,
        disabled=rating is not None,
    )

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_pipeline, tab_compare = st.tabs(["NLP Pipeline", "NLP vs Keyword (side-by-side)"])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — Full NLP pipeline
# ═════════════════════════════════════════════════════════════════════════════
with tab_pipeline:
    if not state:
        st.info("Enter a query above and press **Search** to see the full NLP pipeline.")
    else:
        parsed = state["parsed"]

        # 1. Query understanding
        st.subheader("1. Query understanding")
        c1, c2, c3 = st.columns(3)
        c1.metric(
            "Intent",
            INTENT_LABELS.get(parsed["intent"], parsed["intent"]),
            help=f"Confidence: {parsed['confidence']:.1%}",
        )
        c2.metric("SQL-ready", "Yes" if parsed["sql_ready"] else "No")
        c3.metric("Latency", f"{state['parse_ms']:.0f} ms")

        with st.expander("Extracted filters & generated SQL", expanded=parsed["sql_ready"]):
            st.write("**Filters:**")
            st.json(parsed["filters"] or {"_": "No structured filters extracted"})
            if parsed.get("sql"):
                st.write("**Generated SQL:**")
                st.code(parsed["sql"], language="sql")
                st.write("**Params:**", parsed.get("params", []))
            if parsed.get("schema_errors"):
                st.warning("Schema validation: " + "; ".join(parsed["schema_errors"]))
            if parsed.get("message"):
                st.caption(parsed["message"])

        # 2. Semantic search
        st.subheader("2. Semantic search results")
        sem_json = state["semantic_json"]
        if state["semantic_error"]:
            st.error(f"Semantic search failed: {state['semantic_error']}")
        elif sem_json:
            m1, m2, m3 = st.columns(3)
            m1.metric("Listings returned", sem_json["count"])
            m2.metric("Latency", f"{state['semantic_ms']:.0f} ms")
            m3.metric("Cached", "Yes" if sem_json.get("cached") else "No")

            if sem_json["count"] == 0:
                st.warning("No matching listings.")
            else:
                for item in sem_json["results"]:
                    with st.container(border=True):
                        head_l, head_r = st.columns([6, 1])
                        head_l.markdown(f"**Listing #{item['rank']}**")
                        head_r.metric("Similarity", f"{item['score']:.2f}", label_visibility="visible")

                        if summarize_results:
                            try:
                                summary, _ = api.summarize(item["remarks"], num_sentences=2)
                                st.markdown(f"> {summary['summary']}")
                            except api.APIError as exc:
                                st.caption(f"Summary unavailable ({exc})")

                        with st.expander("Full remarks"):
                            st.write(item["remarks"])

                        if show_compliance:
                            try:
                                comp, _ = api.check_compliance(item["remarks"])
                                if comp["compliant"]:
                                    st.success("Fair Housing: compliant")
                                else:
                                    st.error(
                                        f"Fair Housing: {comp['error_count']} error(s), "
                                        f"{comp['warning_count']} warning(s)"
                                    )
                                    with st.expander("Violations"):
                                        for v in comp["violations"]:
                                            st.markdown(
                                                f"- **{v['category']}** ({v['severity']}): "
                                                f"`{v['matched_text']}` → {v['suggestion']}"
                                            )
                            except api.APIError:
                                pass

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — Side-by-side: NLP-augmented vs keyword-only
# ═════════════════════════════════════════════════════════════════════════════
with tab_compare:
    st.markdown(
        "Same query, two retrieval strategies. **NLP-augmented** uses intent "
        "classification + filter extraction + semantic (FAISS) retrieval. "
        "**Keyword-only** is BM25 over the same corpus — what a basic search "
        "box gives you."
    )

    if not state:
        st.info("Enter a query above and press **Search** to compare retrieval strategies.")
    else:
        sem_json = state["semantic_json"]
        kw_json = state["keyword_json"]
        parsed_cmp = state["parsed"]

        # ── Overlap analysis (by remarks text) ─────────────────────────────
        if sem_json and kw_json:
            sem_remarks = {r["remarks"] for r in sem_json["results"]}
            kw_remarks = {r["remarks"] for r in kw_json["results"]}
            overlap = sem_remarks & kw_remarks
            denom = max(len(sem_remarks), 1)
            overlap_pct = (len(overlap) / denom) * 100

            o1, o2, o3 = st.columns(3)
            o1.metric("Overlap (top-K)", f"{len(overlap)} / {state['top_k']}", help="Listings that appear in both rankings")
            o2.metric("NLP-only", f"{len(sem_remarks - kw_remarks)}")
            o3.metric("Keyword-only", f"{len(kw_remarks - sem_remarks)}")
            st.caption(
                f"_{overlap_pct:.0f}% overlap. Lower overlap usually means the "
                f"two strategies disagree on what's relevant — interesting demo cases live here._"
            )

        st.divider()

        # ── Two-column side-by-side ────────────────────────────────────────
        col_nlp, col_kw = st.columns(2)

        # LEFT: NLP-augmented
        with col_nlp:
            st.markdown("### NLP-augmented")
            st.caption("intent → filter extraction → semantic retrieval (FAISS)")

            if state["semantic_error"]:
                st.error(f"Semantic search failed: {state['semantic_error']}")
            elif sem_json:
                a, b = st.columns(2)
                a.metric("Latency", f"{state['semantic_ms']:.0f} ms")
                b.metric("Results", sem_json["count"])

                st.markdown(
                    f"**Intent:** `{parsed_cmp['intent']}`  "
                    f"({parsed_cmp['confidence']:.0%} confidence)"
                )
                if parsed_cmp.get("filters"):
                    st.markdown("**Extracted filters:**")
                    st.json(parsed_cmp["filters"])
                else:
                    st.caption("_No structured filters extracted._")

                for item in sem_json["results"]:
                    also_in_kw = None
                    if kw_json:
                        for k in kw_json["results"]:
                            if k["remarks"] == item["remarks"]:
                                also_in_kw = k["rank"]
                                break
                    with st.container(border=True):
                        head_l, head_r = st.columns([3, 2])
                        head_l.markdown(f"**#{item['rank']}**")
                        head_r.markdown(f"`score {item['score']:.2f}`")
                        if also_in_kw:
                            st.caption(f"also in keyword results at #{also_in_kw}")
                        else:
                            st.caption("**NLP-only result**")
                        snippet = item["remarks"][:280] + ("..." if len(item["remarks"]) > 280 else "")
                        st.write(snippet)

        # RIGHT: Keyword-only
        with col_kw:
            st.markdown("### Keyword-only (BM25)")
            st.caption("tokenize → BM25 ranking over the same corpus")

            if state["keyword_error"]:
                st.error(f"Keyword search failed: {state['keyword_error']}")
            elif kw_json:
                a, b = st.columns(2)
                a.metric("Latency", f"{state['keyword_ms']:.0f} ms")
                b.metric("Results", kw_json["count"])

                st.markdown("**Intent:** _(not detected — BM25 has no notion of intent)_")
                st.caption("_No filter extraction. Every query is a bag of words._")
                st.write("")

                for item in kw_json["results"]:
                    also_in_nlp = None
                    if sem_json:
                        for s in sem_json["results"]:
                            if s["remarks"] == item["remarks"]:
                                also_in_nlp = s["rank"]
                                break
                    with st.container(border=True):
                        head_l, head_r = st.columns([3, 2])
                        head_l.markdown(f"**#{item['rank']}**")
                        head_r.markdown(f"`score {item['score']:.2f}`")
                        if also_in_nlp:
                            st.caption(f"also in NLP results at #{also_in_nlp}")
                        else:
                            st.caption("**Keyword-only result**")
                        snippet = item["remarks"][:280] + ("..." if len(item["remarks"]) > 280 else "")
                        st.write(snippet)
