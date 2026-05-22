import requests
from urllib.parse import quote

WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
WIKI_SEARCH_URL  = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "CurrentAffairsMitra/1.0 (educational MCP server)"}


class WikiClient:
    def _search_page_title(self, query: str) -> str | None:
        """
        Use the Wikipedia search API to find the most relevant page title for a query.
        Returns the top result's title, or None if nothing found.
        """
        params = {
            "action":   "query",
            "list":     "search",
            "srsearch": query,
            "srlimit":  1,
            "format":   "json",
        }
        try:
            resp = requests.get(WIKI_SEARCH_URL, params=params, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            results = resp.json().get("query", {}).get("search", [])
            if results:
                return results[0]["title"]
        except Exception:
            pass
        return None

    def get_scheme_summary(self, scheme_name: str) -> dict:
        """
        Fetch a concise Wikipedia summary for a government scheme or topic.
        First searches for the best matching page, then fetches its summary.

        Returns a dict with keys: title, summary, url, found (bool).
        """
        # Step 1: resolve to a canonical Wikipedia page title
        page_title = self._search_page_title(scheme_name)
        if not page_title:
            return {
                "found":   False,
                "title":   scheme_name,
                "summary": f"No Wikipedia article found for '{scheme_name}'.",
                "url":     "",
            }

        # Step 2: fetch the page summary
        try:
            url = WIKI_SUMMARY_URL.format(title=quote(page_title, safe=""))
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return {
                "found":   True,
                "title":   data.get("title", page_title),
                "summary": data.get("extract", "No summary available."),
                "url":     data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            }
        except Exception as exc:
            return {
                "found":   False,
                "title":   page_title,
                "summary": f"Error fetching Wikipedia summary: {exc}",
                "url":     "",
            }
