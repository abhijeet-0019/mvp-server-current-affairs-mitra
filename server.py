import os
from mcp.server.fastmcp import FastMCP
from rss_client import NewsClient
from wiki_client import WikiClient

mcp      = FastMCP("Current Affairs Mitra")
news     = NewsClient()
wiki     = WikiClient()


# ---------------------------------------------------------------------------
# Helper — strip internal _dt key before formatting output
# ---------------------------------------------------------------------------
def _clean(entries: list[dict]) -> list[dict]:
    return [{k: v for k, v in e.items() if k != "_dt"} for e in entries]


def _format_entries(entries: list[dict]) -> str:
    if not entries:
        return "No results found."
    lines = []
    for i, e in enumerate(_clean(entries), 1):
        lines.append(
            f"{i}. [{e['source']}] {e['title']}\n"
            f"   Published: {e['published']}\n"
            f"   {e['summary']}\n"
            f"   URL: {e['url']}"
        )
    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 1 — PIB press releases
# ---------------------------------------------------------------------------
@mcp.tool()
def get_daily_pib_releases(date: str = "today", ministry: str = "") -> str:
    """
    Fetch recent official government news from major English newspapers (The Hindu,
    NDTV, Indian Express) — these sources carry full English coverage of government
    announcements, policy launches, cabinet decisions, and scheme updates.
    Note: PIB's public RSS feed is Hindi-only, so English newspaper coverage
    is used as the source for government news.

    Use this tool when the user asks about:
    - What did the government announce today / this week?
    - Any new policy or scheme launched by a ministry?
    - Official government stance on an issue.

    Args:
        date    : "today" (default) for the latest news, or a specific date
                  in YYYY-MM-DD format (e.g. "2026-05-20").
        ministry: optional keyword to filter by ministry name
                  (e.g. "Agriculture", "Finance", "Defence").
                  Leave blank to get all government news.
    """
    entries = news.get_pib_releases(date=date, ministry=ministry)
    if not entries:
        return (
            f"No PIB releases found for date='{date}'"
            + (f", ministry='{ministry}'." if ministry else ".")
            + " Try broadening the date range or removing the ministry filter."
        )
    header = f"PIB press releases (date={date}"
    if ministry:
        header += f", ministry={ministry}"
    header += f") — {len(entries)} result(s):\n\n"
    return header + _format_entries(entries)


# ---------------------------------------------------------------------------
# Tool 2 — Search current affairs
# ---------------------------------------------------------------------------
@mcp.tool()
def search_current_affairs(topic: str, days_back: int = 7) -> str:
    """
    Search recent news articles across PIB, The Hindu, Indian Express, and NDTV
    for a specific topic or keyword.

    Use this tool when the user asks about:
    - Recent developments on a topic (e.g. "GST reform", "India-China relations")
    - Whether something happened recently (e.g. "any news about ISRO this week?")
    - Background context on a current event for exam prep.

    Args:
        topic    : keyword or phrase to search (e.g. "Jal Jeevan Mission",
                   "India GDP growth", "UPSC syllabus change").
        days_back: how many days back to search (default 7; max useful is ~30).
    """
    entries = news.search_current_affairs(topic=topic, days_back=days_back)
    if not entries:
        return (
            f"No recent articles found for '{topic}' in the last {days_back} days. "
            "Try a broader keyword or increase days_back."
        )
    header = f"Search results for '{topic}' (last {days_back} days) — {len(entries)} result(s):\n\n"
    return header + _format_entries(entries)


# ---------------------------------------------------------------------------
# Tool 3 — Government scheme summary via Wikipedia
# ---------------------------------------------------------------------------
@mcp.tool()
def get_scheme_summary(scheme_name: str) -> str:
    """
    Fetch a detailed description of an Indian government scheme or policy from Wikipedia.
    Wikipedia is a reliable free source for scheme objectives, launch dates, beneficiaries,
    budget allocations, and implementing agencies — exactly what UPSC/GS papers test.

    Use this tool when the user asks:
    - "What is [scheme name]?" (e.g. PM-KISAN, Jal Jeevan Mission, PMAY, MNREGA)
    - "Explain the objectives of [scheme]."
    - "Who are the beneficiaries of [scheme]?"
    - Any question requiring factual background on a government programme.

    Args:
        scheme_name: name of the government scheme or policy
                     (e.g. "Pradhan Mantri Jan Dhan Yojana", "Make in India",
                      "National Education Policy 2020").
    """
    result = wiki.get_scheme_summary(scheme_name)
    if not result["found"]:
        return result["summary"]
    return (
        f"**{result['title']}**\n\n"
        f"{result['summary']}\n\n"
        f"Source: {result['url']}"
    )


# ---------------------------------------------------------------------------
# Tool 4 — Fetch full article text
# ---------------------------------------------------------------------------
@mcp.tool()
def get_article_content(url: str) -> str:
    """
    Fetch and return the full readable text of a news article or web page given its URL.
    Use this tool when:
    - The user shares a news link and asks to summarise, analyse, or answer questions about it.
    - A previous tool returned article URLs and the user wants deeper detail on one.
    - The user says "read this article for me" or "what does this link say?".

    Args:
        url: the full URL of the article (e.g. "https://indianexpress.com/article/...").
    """
    try:
        import trafilatura
        html = trafilatura.fetch_url(url)
        if not html:
            return f"Could not fetch content from {url}. The page may require login or is unavailable."
        text = trafilatura.extract(html)
        if not text:
            return f"Page was fetched but no readable article text could be extracted from {url}."
        return f"Article content from {url}:\n\n{text}"
    except Exception as exc:
        return f"Error fetching article: {exc}"


# ---------------------------------------------------------------------------
# Tool 5 — Exam material aggregator (feeds MCQ generation)
# ---------------------------------------------------------------------------
@mcp.tool()
def get_exam_material(topic: str, days_back: int = 7) -> str:
    """
    Aggregate recent PIB press releases and news articles related to a topic to
    provide raw study material. This tool is specifically designed to support
    MCQ generation, quiz creation, and exam-focused study.

    Use this tool when the user asks:
    - "Give me MCQs on [topic]" — call this tool first, then generate questions
      from the returned content.
    - "Create a quiz on [topic] from this week's news."
    - "I want to test myself on [topic] — generate 5 questions."
    - "What should I study about [topic] for UPSC/SSC?"

    After calling this tool, use the returned content to generate multiple-choice
    questions with 4 options (A/B/C/D) and the correct answer clearly marked.

    Args:
        topic    : exam topic or subject area (e.g. "Indian economy", "space missions",
                   "environmental policy", "India's foreign relations").
        days_back: how many days back to look for source material (default 7).
    """
    entries = news.get_exam_material(topic=topic, days_back=days_back)
    if not entries:
        return (
            f"No recent content found for '{topic}' in the last {days_back} days. "
            "Try a broader topic or increase days_back."
        )
    header = (
        f"Exam material on '{topic}' (last {days_back} days) — {len(entries)} source(s).\n"
        "Use the following headlines and summaries to generate MCQs:\n\n"
    )
    return header + _format_entries(entries)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
