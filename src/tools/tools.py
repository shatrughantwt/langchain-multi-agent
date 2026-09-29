from langchain.tools import tool

import os
import re
import requests

from dotenv import load_dotenv
from tavily import TavilyClient
from bs4 import BeautifulSoup
from readability import Document
import trafilatura


# Load environment variables
load_dotenv()

# Create Tavily client
tavily = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


@tool
def web_search(query: str) -> str:
    """
    Search the web for recent and reliable information about a topic.
    Returns titles, URLs, and snippets.
    """

    try:
        results = tavily.search(
            query=query,
            max_results=5
        )

        output = []

        for result in results.get("results", []):
            output.append(
                f"Title: {result.get('title', 'No title')}\n"
                f"URL: {result.get('url', 'No URL')}\n"
                f"Snippet: {result.get('content', '')[:300]}\n"
            )

        if not output:
            return "No search results found."

        return "\n----\n".join(output)

    except Exception as e:
        return f"Web search failed: {str(e)}"


@tool
def scrape_url(url: str) -> str:
    """
    Scrape and extract clean readable content from a URL.

    Uses multiple extraction methods for better reliability.
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }

    try:
        # --------------------------------------------------
        # 1. Fetch page
        # --------------------------------------------------

        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        html = response.text

        # --------------------------------------------------
        # 2. Try Trafilatura first
        # --------------------------------------------------

        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False
        )

        if extracted and len(extracted.strip()) > 200:
            cleaned = re.sub(r"\s+", " ", extracted).strip()
            return cleaned[:5000]

        # --------------------------------------------------
        # 3. Try Readability + BeautifulSoup
        # --------------------------------------------------

        doc = Document(html)

        clean_html = doc.summary()

        soup = BeautifulSoup(
            clean_html,
            "html.parser"
        )

        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form"
        ]):
            tag.decompose()

        text = soup.get_text(
            separator=" ",
            strip=True
        )

        if text and len(text.strip()) > 200:
            cleaned = re.sub(r"\s+", " ", text).strip()
            return cleaned[:5000]

        # --------------------------------------------------
        # 4. Final BeautifulSoup fallback
        # --------------------------------------------------

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form"
        ]):
            tag.decompose()

        text = soup.get_text(
            separator=" ",
            strip=True
        )

        cleaned = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        if cleaned:
            return cleaned[:5000]

        return "Could not extract meaningful content from the page."

    # ------------------------------------------------------
    # Error handling
    # ------------------------------------------------------

    except requests.exceptions.Timeout:
        return "Request timed out while scraping the URL."

    except requests.exceptions.HTTPError as e:
        return f"HTTP error occurred: {e}"

    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"

    except Exception as e:
        return f"Could not scrape URL: {e}"