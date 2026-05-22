"""
Unit tests for all 5 MCP tools in server.py.
Strategy: patch NewsClient and WikiClient methods directly so no network calls are made.
"""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Make project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server
from tests.mock_data import (
    PIB_ENTRIES, INDIA_ENTRIES, ECONOMY_ENTRIES,
    WIKI_SEARCH_RESPONSE, WIKI_SUMMARY_RESPONSE,
    MOCK_ARTICLE_HTML,
)

# ---------------------------------------------------------------------------
# Helpers — normalise raw mock entries through the real _normalize() pipeline
# ---------------------------------------------------------------------------
from rss_client import _normalize


def pib_normalized():
    return [_normalize(e, "PIB") for e in PIB_ENTRIES]


def india_normalized():
    return [_normalize(e, "The Hindu – National") for e in INDIA_ENTRIES]


def economy_normalized():
    return [_normalize(e, "The Hindu – Business") for e in ECONOMY_ENTRIES]


# ===========================================================================
# Tool 1: get_daily_pib_releases
# ===========================================================================
class TestGetDailyPibReleases:
    def test_returns_formatted_results(self):
        with patch.object(server.news, "get_pib_releases", return_value=pib_normalized()):
            result = server.get_daily_pib_releases()
        assert "Jal Jeevan Mission" in result
        assert "National Quantum Mission" in result
        assert "PIB" in result

    def test_shows_count_in_header(self):
        with patch.object(server.news, "get_pib_releases", return_value=pib_normalized()):
            result = server.get_daily_pib_releases()
        assert "3 result(s)" in result

    def test_no_results_returns_helpful_message(self):
        with patch.object(server.news, "get_pib_releases", return_value=[]):
            result = server.get_daily_pib_releases(date="2020-01-01")
        assert "No PIB releases found" in result

    def test_ministry_filter_reflected_in_output(self):
        filtered = [pib_normalized()[2]]  # GST/Finance entry
        with patch.object(server.news, "get_pib_releases", return_value=filtered):
            result = server.get_daily_pib_releases(ministry="Finance")
        assert "GST" in result

    def test_no_results_with_ministry_shows_suggestion(self):
        with patch.object(server.news, "get_pib_releases", return_value=[]):
            result = server.get_daily_pib_releases(ministry="UnknownMinistry")
        assert "ministry filter" in result or "ministry" in result.lower()


# ===========================================================================
# Tool 2: search_current_affairs
# ===========================================================================
class TestSearchCurrentAffairs:
    def test_returns_results_for_matching_topic(self):
        with patch.object(server.news, "search_current_affairs", return_value=india_normalized()):
            result = server.search_current_affairs("ISRO")
        assert "ISRO" in result
        assert "Gaganyaan" in result

    def test_shows_result_count(self):
        with patch.object(server.news, "search_current_affairs", return_value=india_normalized()):
            result = server.search_current_affairs("economy")
        assert "2 result(s)" in result

    def test_no_results_returns_helpful_message(self):
        with patch.object(server.news, "search_current_affairs", return_value=[]):
            result = server.search_current_affairs("nonexistent topic xyz")
        assert "No recent articles found" in result

    def test_days_back_reflected_in_header(self):
        with patch.object(server.news, "search_current_affairs", return_value=india_normalized()):
            result = server.search_current_affairs("India", days_back=14)
        assert "14 days" in result

    def test_url_included_in_output(self):
        with patch.object(server.news, "search_current_affairs", return_value=india_normalized()):
            result = server.search_current_affairs("India")
        assert "https://" in result


# ===========================================================================
# Tool 3: get_scheme_summary
# ===========================================================================
class TestGetSchemeSummary:
    def _mock_wiki_result(self):
        return {
            "found":   True,
            "title":   "Jal Jeevan Mission",
            "summary": WIKI_SUMMARY_RESPONSE["extract"],
            "url":     "https://en.wikipedia.org/wiki/Jal_Jeevan_Mission",
        }

    def test_returns_title_and_summary(self):
        with patch.object(server.wiki, "get_scheme_summary", return_value=self._mock_wiki_result()):
            result = server.get_scheme_summary("Jal Jeevan Mission")
        assert "Jal Jeevan Mission" in result
        assert "drinking water" in result.lower()

    def test_includes_wikipedia_url(self):
        with patch.object(server.wiki, "get_scheme_summary", return_value=self._mock_wiki_result()):
            result = server.get_scheme_summary("Jal Jeevan Mission")
        assert "wikipedia.org" in result

    def test_not_found_returns_message(self):
        with patch.object(server.wiki, "get_scheme_summary", return_value={
            "found": False,
            "title": "XYZ Unknown Scheme",
            "summary": "No Wikipedia article found for 'XYZ Unknown Scheme'.",
            "url": "",
        }):
            result = server.get_scheme_summary("XYZ Unknown Scheme")
        assert "No Wikipedia article found" in result

    def test_scheme_budget_info_present(self):
        with patch.object(server.wiki, "get_scheme_summary", return_value=self._mock_wiki_result()):
            result = server.get_scheme_summary("Jal Jeevan Mission")
        assert "3.60 lakh crore" in result or "lakh crore" in result


# ===========================================================================
# Tool 4: get_article_content
# ===========================================================================
class TestGetArticleContent:
    def test_returns_extracted_text(self):
        with patch("trafilatura.fetch_url", return_value=MOCK_ARTICLE_HTML), \
             patch("trafilatura.extract", return_value="India crossed 100 GW of installed solar capacity."):
            result = server.get_article_content("https://example.com/solar")
        assert "100 GW" in result
        assert "solar" in result.lower()

    def test_fetch_failure_returns_error_message(self):
        with patch("trafilatura.fetch_url", return_value=None):
            result = server.get_article_content("https://example.com/broken")
        assert "Could not fetch" in result

    def test_extraction_failure_returns_error_message(self):
        with patch("trafilatura.fetch_url", return_value=b"<html></html>"), \
             patch("trafilatura.extract", return_value=None):
            result = server.get_article_content("https://example.com/empty")
        assert "no readable article text" in result.lower()

    def test_exception_returns_graceful_error(self):
        with patch("trafilatura.fetch_url", side_effect=Exception("network error")):
            result = server.get_article_content("https://example.com/err")
        assert "Error fetching article" in result

    def test_url_included_in_output(self):
        with patch("trafilatura.fetch_url", return_value=MOCK_ARTICLE_HTML), \
             patch("trafilatura.extract", return_value="Some article text."):
            result = server.get_article_content("https://example.com/article")
        assert "https://example.com/article" in result


# ===========================================================================
# Tool 5: get_exam_material
# ===========================================================================
class TestGetExamMaterial:
    def test_returns_content_for_topic(self):
        combined = pib_normalized() + india_normalized()
        with patch.object(server.news, "get_exam_material", return_value=combined):
            result = server.get_exam_material("ISRO space")
        assert "Jal Jeevan Mission" in result or "ISRO" in result

    def test_shows_source_count(self):
        combined = pib_normalized() + india_normalized()
        with patch.object(server.news, "get_exam_material", return_value=combined):
            result = server.get_exam_material("Indian economy")
        assert "5 source(s)" in result

    def test_contains_mcq_instruction_hint(self):
        combined = pib_normalized()
        with patch.object(server.news, "get_exam_material", return_value=combined):
            result = server.get_exam_material("government scheme")
        assert "MCQ" in result or "mcq" in result.lower()

    def test_no_results_returns_helpful_message(self):
        with patch.object(server.news, "get_exam_material", return_value=[]):
            result = server.get_exam_material("completely obscure topic xyz123")
        assert "No recent content found" in result

    def test_days_back_passed_through(self):
        """Verify days_back arg is forwarded to the client method."""
        with patch.object(server.news, "get_exam_material", return_value=pib_normalized()) as mock_method:
            server.get_exam_material("economy", days_back=14)
        mock_method.assert_called_once_with(topic="economy", days_back=14)
