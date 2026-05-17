# Week 11 Demo Video — Script & Shot List

**Target length:** 3:45 (within the 3–5 min brief)
**Setup:** Browser at `https://<your-app>.streamlit.app`, full-screen, no other tabs visible. Mic on, system notifications off, 1.5× browser zoom for projector clarity.

## Pre-recording checklist

- [ ] Hit Render `/health` 60 seconds before recording (free tier spins down after 15 min idle; cold start is ~30s)
- [ ] Open metrics page → **Reset metrics** → confirm (clean slate)
- [ ] Run one warmup query in private so subsequent queries are cache-hot
- [ ] Close Slack, Discord, email — no notification sounds
- [ ] Test mic levels with a 5-second test recording

---

## 0:00 – 0:20 — Hook

**Narration:**
> When someone shops for a home, they describe it in plain English — *"cozy starter home with a big yard"*. But most MLS search boxes only understand keywords or rigid dropdowns. Over the last twelve weeks I built a system that reads natural language, extracts structured filters, and ranks listings by what the buyer actually means.

**Shot:**
Streamlit app loaded, default query visible. Slow zoom on the search box.

---

## 0:20 – 0:55 — Filter extraction win

**Narration:**
> Let's start with a structured query.

**Action:** Click example chip **"3 bed 2 bath under 700k in Irvine"** → click **Search**.

**Narration:**
> The intent classifier flags this as 'ready to buy' with 97% confidence. The filter extractor pulls out bedrooms, price, and city, and generates a parameterized SQL query — no hardcoded forms, no dropdowns. The semantic ranker then returns five listings, each with an extractive summary and a Fair Housing compliance check.

**Action:** Expand the SQL panel. Highlight the generated SQL. Scroll down one result, briefly point at the summary + green compliant badge.

---

## 0:55 – 1:30 — Intent gating

**Narration:**
> Not every query is a filter. Sometimes buyers are still researching.

**Action:** Click example chip **"what makes Anaheim a good place to buy?"** → **Search**.

**Narration:**
> Same input box — but the classifier recognizes this is informational, doesn't try to generate bogus SQL, and falls back to semantic retrieval over neighborhood listings. The system knows when to filter and when to explore.

**Shot:** Point at intent=`researching` and SQL-ready=`No`.

---

## 1:30 – 2:30 — Side-by-side: the value prop

**Action:** Click the **"NLP vs Keyword"** tab. Click example **"cozy starter home with a big yard"** → **Search**.

**Narration:**
> Here's the real test. The same query, two retrieval strategies. On the left, our NLP pipeline — intent, filters, semantic search. On the right, plain BM25 keyword search over the same listings.

**Action:** Pause on the overlap counter. Point at "1 of 5" or whatever it shows.

**Narration:**
> Only one listing appears in both rankings. BM25 is fixated on the literal words 'cozy' and 'yard'. The semantic model understands that 'starter home' is about price tier and condition, not exact keywords — so it surfaces homes BM25 misses entirely.

**Action:** Scroll through 2–3 result pairs to show the contrast.

---

## 2:30 – 3:15 — Metrics + production-readiness

**Action:** Scroll up, click **Helpful** on the rating banner. Open sidebar → **Open metrics dashboard**.

**Narration:**
> Every query is logged with latency and intent. Users can rate results, giving us a satisfaction proxy. Over a typical session, semantic search runs in around 600 milliseconds and 'ready to buy' is the dominant intent. The API is rate-limited, cached, Dockerized, and deployed to Render — the UI lives on Streamlit Cloud.

**Shot:** Brief pan over the dashboard charts.

---

## 3:15 – 3:45 — Outro

**Narration:**
> Twelve weeks: taxonomy, cleaning, entity and signal extraction, intent classification, semantic search with FAISS, extractive summarization, Fair Housing compliance, FastAPI, and now an end-to-end demo. The source is on GitHub at `qiwen-wen/real-estate-nlp`.

**Shot:** Close-up of the GitHub URL or repo screenshot.

---

## Recording tips

- Use OBS or QuickTime, 1080p, 30fps
- Record at 1.5× browser zoom so the SQL panel + result cards read clearly on a projector
- One clean take then trim — re-records of single sections rarely cut together cleanly
- If anything cold-starts mid-demo: pause, narrate one extra sentence over the loading spinner ("first query warms up the embedding model"), keep going

## Backup queries

If the canned ones underperform on the day, swap in:
- "single-story home with pool and updated kitchen" — usually strong semantic-vs-keyword contrast
- "starter condo under 500k near good schools" — exercises both filter extraction and semantic ranking
