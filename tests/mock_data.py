"""
Mock data for unit tests.
All feedparser entries are plain dicts that mirror the subset of attributes
actually accessed by NewsClient._normalize() and the tool functions.
"""
from datetime import datetime, timezone
import time


def _make_entry(title, link, summary, pub_dt: datetime):
    """Build a minimal feedparser-like entry dict."""
    tt = pub_dt.timetuple()
    return type("Entry", (), {
        "title":            title,
        "link":             link,
        "summary":          summary,
        "published_parsed": time.struct_time((*tt[:6], 0, 0, 0)),
        "get":              lambda self, k, d="": getattr(self, k, d),
    })()


# ---------------------------------------------------------------------------
# PIB entries
# ---------------------------------------------------------------------------
PIB_ENTRIES = [
    _make_entry(
        "PM launches Jal Jeevan Mission Phase 2",
        "https://pib.gov.in/article/jjm-phase2",
        "The Prime Minister today launched Phase 2 of Jal Jeevan Mission targeting 5 crore households.",
        datetime(2026, 5, 22, 9, 0, tzinfo=timezone.utc),
    ),
    _make_entry(
        "Cabinet approves National Quantum Mission",
        "https://pib.gov.in/article/quantum-mission",
        "Union Cabinet approved Rs 6003 crore National Quantum Mission for 2023-31.",
        datetime(2026, 5, 22, 10, 30, tzinfo=timezone.utc),
    ),
    _make_entry(
        "Ministry of Finance releases GST collection data",
        "https://pib.gov.in/article/gst-may-2026",
        "GST collection for May 2026 stands at Rs 1.87 lakh crore, 12% higher than last year.",
        datetime(2026, 5, 21, 14, 0, tzinfo=timezone.utc),
    ),
]

# ---------------------------------------------------------------------------
# India news entries (The Hindu / Indian Express / NDTV)
# ---------------------------------------------------------------------------
INDIA_ENTRIES = [
    _make_entry(
        "ISRO successfully tests Gaganyaan crew module",
        "https://thehindu.com/sci-tech/isro-gaganyaan-test",
        "ISRO conducted a successful abort test of the Gaganyaan crew module off the coast of Sriharikota.",
        datetime(2026, 5, 21, 8, 0, tzinfo=timezone.utc),
    ),
    _make_entry(
        "India's GDP growth forecast revised upward to 7.2%",
        "https://indianexpress.com/economy/gdp-growth-2026",
        "IMF has revised India's GDP growth forecast for 2026-27 upward to 7.2% citing strong domestic demand.",
        datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc),
    ),
]

# ---------------------------------------------------------------------------
# Economy entries
# ---------------------------------------------------------------------------
ECONOMY_ENTRIES = [
    _make_entry(
        "RBI holds repo rate at 6.25%",
        "https://thehindu.com/business/rbi-mpc-june-2026",
        "The Reserve Bank of India MPC unanimously decided to hold the repo rate at 6.25% in its June 2026 meeting.",
        datetime(2026, 5, 22, 11, 0, tzinfo=timezone.utc),
    ),
]

# ---------------------------------------------------------------------------
# Wikipedia mock response
# ---------------------------------------------------------------------------
WIKI_SEARCH_RESPONSE = {
    "query": {
        "search": [
            {"title": "Jal Jeevan Mission", "snippet": "Jal Jeevan Mission is a Government of India initiative..."}
        ]
    }
}

WIKI_SUMMARY_RESPONSE = {
    "title":   "Jal Jeevan Mission",
    "extract": (
        "Jal Jeevan Mission (JJM) is a Government of India initiative launched in 2019 "
        "to provide safe and adequate drinking water through individual household tap "
        "connections by 2024 to all households in rural India. The mission operates "
        "under the Department of Drinking Water and Sanitation with a budget outlay "
        "of ₹3.60 lakh crore."
    ),
    "content_urls": {
        "desktop": {"page": "https://en.wikipedia.org/wiki/Jal_Jeevan_Mission"}
    },
}

# ---------------------------------------------------------------------------
# Article HTML mock (for trafilatura extraction)
# ---------------------------------------------------------------------------
MOCK_ARTICLE_HTML = b"""
<html><body>
<article>
<h1>India achieves record solar capacity</h1>
<p>India crossed 100 GW of installed solar capacity on Thursday, a major milestone
in its clean energy transition. The government aims to reach 500 GW of renewable
energy by 2030 as part of its Paris Agreement commitments.</p>
<p>Solar power now accounts for 18% of India's total installed electricity generation
capacity, up from just 2% a decade ago.</p>
</article>
</body></html>
"""
