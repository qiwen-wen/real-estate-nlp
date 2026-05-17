"""Metrics dashboard — reads demo_queries.jsonl + demo_ratings.jsonl.

Shows query volume, latency distribution, satisfaction rate, intent mix,
and the most recent searches. Native Streamlit charts only — no Plotly dep.
"""

import os
import sys

# `streamlit run` runs this from .../scripts/demo/, so we're two extra levels
# down from the project root compared to app.py.
_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _BASE not in sys.path:
    sys.path.append(_BASE)

import pandas as pd
import streamlit as st

from scripts.demo import metrics_log

st.set_page_config(page_title="Demo Metrics", layout="wide")
st.title("Demo Metrics")
st.caption(
    "Query volume, latency, and user satisfaction across the demo session. "
    "Data persists across reloads (JSONL files in `results/`)."
)

searches = pd.DataFrame(metrics_log.read_searches())
ratings = pd.DataFrame(metrics_log.read_ratings())

if searches.empty:
    st.info("No queries logged yet. Run some searches on the main page, then come back.")
    st.page_link("app.py", label="← Back to search")
    st.stop()

searches["timestamp"] = pd.to_datetime(searches["timestamp"])
if not ratings.empty:
    ratings["timestamp"] = pd.to_datetime(ratings["timestamp"])

# ── Headline metrics ─────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total queries", len(searches))

sem_p50 = searches["semantic_ms"].median()
kw_p50 = searches["keyword_ms"].median()
c2.metric("Semantic p50", f"{sem_p50:.0f} ms" if pd.notna(sem_p50) else "—")
c3.metric("Keyword p50", f"{kw_p50:.0f} ms" if pd.notna(kw_p50) else "—")

if not ratings.empty:
    pos = int((ratings["rating"] == "up").sum())
    pct = (pos / len(ratings)) * 100
    c4.metric(
        "Satisfaction",
        f"{pct:.0f}%",
        help=f"{pos} helpful out of {len(ratings)} rated searches",
    )
else:
    c4.metric("Satisfaction", "—", help="No ratings yet — rate a search on the main page")

st.divider()

# ── Latency: semantic vs keyword ─────────────────────────────────────────────
st.subheader("Latency: semantic vs keyword (ms)")
latency_df = searches[["semantic_ms", "keyword_ms"]].dropna()
if latency_df.empty:
    st.caption("Not enough data to chart latency yet.")
else:
    rows = pd.DataFrame({
        "Semantic": [
            latency_df["semantic_ms"].median(),
            latency_df["semantic_ms"].quantile(0.95),
        ],
        "Keyword": [
            latency_df["keyword_ms"].median(),
            latency_df["keyword_ms"].quantile(0.95),
        ],
    }, index=["p50", "p95"])
    st.bar_chart(rows)
    st.caption(
        f"Semantic search is slower (it runs a transformer encoder); "
        f"keyword search is lighter but doesn't understand synonyms or intent."
    )

# ── Query volume over time ───────────────────────────────────────────────────
st.subheader("Query volume")
# Resample to per-minute counts so the chart looks reasonable even with sparse data
vol = searches.set_index("timestamp").resample("1min").size()
vol.name = "queries"
if vol.empty or vol.max() == 0:
    st.caption("No queries to chart yet.")
else:
    st.line_chart(vol)

# ── Intent distribution ──────────────────────────────────────────────────────
st.subheader("Intent distribution")
intent_counts = searches["intent"].value_counts()
st.bar_chart(intent_counts)
sql_ready_rate = (searches["sql_ready"].sum() / len(searches)) * 100
st.caption(f"{sql_ready_rate:.0f}% of queries produced SQL-ready filter extractions.")

# ── Top queries ──────────────────────────────────────────────────────────────
st.subheader("Top queries")
top = (
    searches["query"]
    .value_counts()
    .head(10)
    .rename_axis("query")
    .reset_index(name="count")
)
st.dataframe(top, hide_index=True, use_container_width=True)

# ── Recent activity ──────────────────────────────────────────────────────────
st.subheader("Recent searches")
recent_cols = ["timestamp", "query", "intent", "result_count", "semantic_ms", "keyword_ms"]
recent = (
    searches.sort_values("timestamp", ascending=False)
    .head(20)[recent_cols]
)
st.dataframe(recent, hide_index=True, use_container_width=True)

# ── Reset (handy for clean demo recordings) ──────────────────────────────────
with st.expander("Reset metrics"):
    st.caption(
        "Deletes the JSONL files. Useful when you want a clean slate before "
        "recording the demo video."
    )
    if st.button("Delete all logged metrics", type="secondary"):
        for path in (metrics_log.SEARCHES_LOG, metrics_log.RATINGS_LOG):
            if os.path.exists(path):
                os.remove(path)
        st.success("Cleared. Refresh the page to see the empty state.")
