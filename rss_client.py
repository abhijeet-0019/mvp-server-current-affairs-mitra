import feedparser
import requests
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Feed registry
# key   → category label exposed to MCP tools
# value → list of (human-readable source name, RSS URL) tuples
# ---------------------------------------------------------------------------
# PIB RSS notes:
# - The feed publishes in both Hindi and English (mixed, based on what was released recently)
# - Entries have no <pubDate> tag — _parse_date() returns datetime.now() as fallback
# - Article pages are iframe-based so trafilatura cannot extract their content
# - English entries are filtered using an ASCII-ratio heuristic (>80% ASCII = English)
# - Newspaper feeds (The Hindu, NDTV, Indian Express) are used alongside PIB to ensure
#   reliable English coverage with summaries and dates.
FEEDS: dict[str, list[tuple[str, str]]] = {
    "government": [
        ("PIB",                   "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3&reg=3"),
        ("The Hindu – National",  "https://www.thehindu.com/news/national/feeder/default.rss"),
        ("NDTV – India",          "https://feeds.feedburner.com/ndtvnews-india-news"),
        ("Indian Express – India", "https://indianexpress.com/section/india/feed/"),
    ],
    "india": [
        ("The Hindu – National", "https://www.thehindu.com/news/national/feeder/default.rss"),
        ("Indian Express – India", "https://indianexpress.com/section/india/feed/"),
        ("NDTV – India",          "https://feeds.feedburner.com/ndtvnews-india-news"),
    ],
    "economy": [
        ("The Hindu – Business",  "https://www.thehindu.com/business/feeder/default.rss"),
        ("Indian Express – Business", "https://indianexpress.com/section/business/feed/"),
    ],
    "science": [
        ("The Hindu – Sci-Tech",  "https://www.thehindu.com/sci-tech/feeder/default.rss"),
        ("Indian Express – Technology", "https://indianexpress.com/section/technology/feed/"),
    ],
    "world": [
        ("The Hindu – World",     "https://www.thehindu.com/news/international/feeder/default.rss"),
        ("Indian Express – World", "https://indianexpress.com/section/world/feed/"),
    ],
    "sports": [
        ("NDTV – Sports",         "https://feeds.feedburner.com/ndtvnews-sports"),
        ("Indian Express – Sports", "https://indianexpress.com/section/sports/feed/"),
    ],
}

# Feeds used for daily digest (one entry per major source)
DIGEST_FEEDS: list[tuple[str, str]] = [
    ("The Hindu",      "https://www.thehindu.com/feeder/default.rss"),
    ("Indian Express", "https://indianexpress.com/feed/"),
    ("NDTV",           "https://feeds.feedburner.com/ndtvnews-top-stories"),
]

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/xml, text/xml, */*"}


def _is_english(text: str) -> bool:
    """Return True if text is predominantly ASCII (i.e. English, not Hindi/Devanagari)."""
    if not text:
        return True
    return sum(1 for c in text if ord(c) < 128) / len(text) > 0.8


def _parse_date(entry) -> datetime:
    """Return a timezone-aware UTC datetime from a feedparser entry.
    Falls back to 'now' when the feed omits <pubDate> — treating undated
    entries as current so they are never silently dropped by recency filters.
    """
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def _normalize(entry, source_name: str) -> dict:
    """Convert a feedparser entry into a plain dict with consistent keys."""
    summary = ""
    if hasattr(entry, "summary"):
        # Strip HTML tags from summary (rough but avoids extra dependencies)
        import re
        summary = re.sub(r"<[^>]+>", "", entry.summary).strip()

    return {
        "title":    entry.get("title", "").strip(),
        "source":   source_name,
        "url":      entry.get("link", ""),
        "summary":  summary[:300],          # cap at 300 chars to keep output manageable
        "published": _parse_date(entry).strftime("%d %b %Y, %H:%M UTC"),
        "_dt":      _parse_date(entry),     # kept for sorting, not shown in output
    }


class NewsClient:
    def fetch_feed(self, url: str, source_name: str) -> list[dict]:
        """Parse a single RSS feed and return normalised article dicts."""
        try:
            # feedparser can use a Request object so we can pass headers
            req = requests.get(url, headers=HEADERS, timeout=10)
            req.raise_for_status()
            feed = feedparser.parse(req.content)
        except Exception:
            return []

        return [_normalize(e, source_name) for e in feed.entries]

    # ------------------------------------------------------------------
    # Tool-level methods (called from server.py)
    # ------------------------------------------------------------------

    def get_pib_releases(self, date: str = "today", ministry: str = "") -> list[dict]:
        """
        Fetch official government news from major English newspapers (The Hindu,
        NDTV, Indian Express) which cover government announcements, policy launches,
        and scheme updates in English with context.
        date    : "today" (default) or "YYYY-MM-DD"
        ministry: optional keyword to filter by ministry name in title/summary
        Returns up to 20 most recent matching entries.
        """
        entries: list[dict] = []
        for source_name, url in FEEDS["government"]:
            entries.extend(self.fetch_feed(url, source_name))

        if date and date.lower() != "today":
            try:
                cutoff = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                entries = [e for e in entries if e["_dt"].date() == cutoff.date()]
            except ValueError:
                pass  # ignore bad date format, return all
        else:
            # "today" → last 48 h (PIB sometimes publishes late evening, buffer helps)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
            entries = [e for e in entries if e["_dt"] >= cutoff]

        if ministry:
            kw = ministry.lower()
            entries = [
                e for e in entries
                if kw in e["title"].lower() or kw in e["summary"].lower()
            ]

        entries.sort(key=lambda e: e["_dt"], reverse=True)
        return entries[:20]

    def search_current_affairs(self, topic: str, days_back: int = 7) -> list[dict]:
        """
        Search title + summary across ALL feeds for `topic`.
        Returns up to 15 results sorted by recency.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        kw = topic.lower()
        results: list[dict] = []
        seen_urls: set[str] = set()

        all_feeds: list[tuple[str, str]] = []
        for source_list in FEEDS.values():
            all_feeds.extend(source_list)
        # deduplicate feed URLs (some appear in multiple categories)
        seen_feed_urls: set[str] = set()
        unique_feeds = [(name, url) for name, url in all_feeds if not (url in seen_feed_urls or seen_feed_urls.add(url))]  # type: ignore[func-returns-value]

        for source_name, url in unique_feeds:
            for entry in self.fetch_feed(url, source_name):
                if entry["url"] in seen_urls:
                    continue
                if entry["_dt"] < cutoff:
                    continue
                if kw in entry["title"].lower() or kw in entry["summary"].lower():
                    results.append(entry)
                    seen_urls.add(entry["url"])

        results.sort(key=lambda e: e["_dt"], reverse=True)
        return results[:15]

    def get_exam_material(self, topic: str, days_back: int = 7) -> list[dict]:
        """
        Aggregate PIB + all news feeds for `topic` — broader than search_current_affairs
        because it returns ALL entries from PIB regardless of keyword match (PIB is
        always exam-relevant) and keyword-matched entries from news feeds.
        Used to feed Claude with raw material for MCQ generation.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        kw = topic.lower()
        results: list[dict] = []
        seen_urls: set[str] = set()

        # 1. All recent PIB entries (they're all potentially exam-relevant)
        for entry in self.fetch_feed(
            "https://www.pib.gov.in/RssMain.aspx?ModID=6&Lang=1&Regid=3", "PIB"
        ):
            if entry["_dt"] >= cutoff and entry["url"] not in seen_urls:
                results.append(entry)
                seen_urls.add(entry["url"])

        # 2. Keyword-matched entries from other feeds
        for source_list in FEEDS.values():
            for source_name, url in source_list:
                if "pib.gov.in" in url:
                    continue
                for entry in self.fetch_feed(url, source_name):
                    if entry["url"] in seen_urls:
                        continue
                    if entry["_dt"] < cutoff:
                        continue
                    if kw in entry["title"].lower() or kw in entry["summary"].lower():
                        results.append(entry)
                        seen_urls.add(entry["url"])

        results.sort(key=lambda e: e["_dt"], reverse=True)
        return results[:25]

    def get_digest(self) -> dict[str, list[dict]]:
        """
        Return top 3 entries from each of the DIGEST_FEEDS sources.
        Used by the daily_digest tool.
        """
        digest: dict[str, list[dict]] = {}
        for source_name, url in DIGEST_FEEDS:
            entries = self.fetch_feed(url, source_name)
            entries.sort(key=lambda e: e["_dt"], reverse=True)
            digest[source_name] = entries[:3]
        return digest
