# Current Affairs Mitra

An MCP server that lets you ask Claude questions about Indian current affairs, government schemes, and daily news — and get answers grounded in real sources.

> "What did the government announce today?"  
> "What is the Jal Jeevan Mission?"  
> "Give me 5 MCQs on India's space program from this week's news."

Built as a learning project to explore MCP. The target audience is UPSC/SSC/competitive exam aspirants who need an interactive, conversational way to engage with current affairs instead of passively reading.

---

## What it does

Wraps three free public data sources — PIB (Press Information Bureau), major Indian news RSS feeds, and Wikipedia — into 5 MCP tools that Claude can call during a conversation:

| Tool | What it answers |
|---|---|
| `get_daily_pib_releases` | Official government announcements and policy launches (via English newspaper coverage) |
| `search_current_affairs` | Recent news on any topic across PIB + major papers |
| `get_scheme_summary` | Objectives, budget, beneficiaries of any government scheme |
| `get_article_content` | Full text of an article given its URL |
| `get_exam_material` | Raw material Claude uses to generate MCQs and quizzes |

No API key needed. All sources are public.

---

## Stack

- Python + [MCP SDK](https://github.com/modelcontextprotocol/python-sdk) (FastMCP)
- `feedparser` for RSS parsing (The Hindu, Indian Express, NDTV)
- `trafilatura` for article text extraction
- `requests` for Wikipedia API calls
- Claude Desktop as the MCP host (stdio transport)
- Data: PIB RSS, The Hindu, Indian Express, NDTV, Wikipedia REST API

---

## Setup

**1. Clone and install**
```bash
git clone https://github.com/abhijeet-0019/mvp-server-current-affairs-mitra.git
cd mvp-server-current-affairs-mitra
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

**2. Register with Claude Desktop**  
Add to `claude_desktop_config.json` (found at `%APPDATA%\Claude\` on Windows):
```json
"mcpServers": {
  "current-affairs-mitra": {
    "command": "C:/path/to/venv/Scripts/python.exe",
    "args": ["C:/path/to/server.py"]
  }
}
```

**3. Restart Claude Desktop**  
The 5 tools will appear in Claude's tool panel automatically.

---

## Run tests

```bash
.\venv\Scripts\python.exe -m pytest tests/test_tools.py -v
```

24 tests, no network calls (all mocked).

---

## Demo queries

- "What are today's top PIB announcements?"
- "Explain the PM Vishwakarma scheme"
- "Any news about ISRO this week?"
- "Summarise this article: [URL]"
- "Give me 5 MCQs on India's environmental policy from this week"

---

## Contributing

This started as a learning project but the use case is real — millions of students preparing for UPSC/SSC spend hours manually going through PIB, newspapers, and government portals. If you want to extend it, some directions worth exploring:

- **Ministry-specific PIB feeds** — PIB has per-ministry RSS; routing queries to the right feed would improve precision
- **State PSC relevance filter** — tag articles by state so students can filter for state-level exams (MPSC, UPPSC, etc.)
- **MCQ difficulty levels** — easy/medium/hard based on topic complexity
- **Answer explanation mode** — after generating MCQs, explain why each answer is correct with source citations
- **Vernacular language support** — many aspirants are more comfortable in Hindi or regional languages

PRs and issues welcome.

---

## Data sources

- [The Hindu](https://thehindu.com), [Indian Express](https://indianexpress.com), [NDTV](https://ndtv.com) — public RSS feeds (English, dated, verified live)
- [Wikipedia REST API](https://en.wikipedia.org/api/rest_v1/) — free, no key required

> **Note on PIB**: PIB's public RSS feed (`pib.gov.in`) is Hindi-only and omits publication dates, making it unsuitable for this server. English government news is sourced from major newspapers that cover PIB releases with full context.
