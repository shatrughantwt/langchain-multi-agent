import os
import re

import requests
import trafilatura

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_core.documents import Document
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from readability import Document as ReadabilityDocument
from tavily import TavilyClient


load_dotenv()


TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY is not set in .env")


tavily = TavilyClient(api_key=TAVILY_API_KEY)


# The Groq free tier allows only 8000 tokens per minute, so every tool
# result has to stay small. Long tool output also bloats the agent
# context on every follow-up turn.
MAX_SEARCH_SNIPPET_CHARS = 600
MAX_SEARCH_TOTAL_CHARS = 4000
MAX_PAGE_CHARS = 6000


@tool
def web_search(query: str) -> str:
    """
    Search the web for recent and relevant information.
    """

    try:
        response = tavily.search(
            query=query,
            max_results=5,
            search_depth="advanced",
        )

        results = response.get("results", [])

        if not results:
            return "No search results found."

        formatted_results = []

        for i, result in enumerate(results, start=1):
            title = result.get("title", "No title")
            url = result.get("url", "No URL")
            content = result.get("content", "No content")

            content = re.sub(r"\s+", " ", content).strip()

            if len(content) > MAX_SEARCH_SNIPPET_CHARS:
                content = content[:MAX_SEARCH_SNIPPET_CHARS] + " ..."

            formatted_results.append(
                f"""
Result {i}
Title: {title}
URL: {url}
Content: {content}
"""
            )

        return "\n".join(formatted_results)[:MAX_SEARCH_TOTAL_CHARS]

    except Exception as e:
        return f"Web search failed: {str(e)}"


@tool
def scrape_url(url: str) -> str:
    """
    Scrape and extract readable text from a webpage.
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/154.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.google.com/",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=15,
        )

        response.raise_for_status()

        html = response.text

        # -----------------------------------------
        # Method 1: trafilatura
        # -----------------------------------------

        extracted_text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            include_links=True,
        )

        if extracted_text:
            cleaned_text = re.sub(r"\s+", " ", extracted_text).strip()

            if len(cleaned_text) > 200:
                return cleaned_text[:MAX_PAGE_CHARS]

        # -----------------------------------------
        # Method 2: readability + BeautifulSoup
        # -----------------------------------------

        readability_doc = ReadabilityDocument(html)

        readable_html = readability_doc.summary()

        soup = BeautifulSoup(readable_html, "html.parser")

        text = soup.get_text(
            separator=" ",
            strip=True,
        )

        text = re.sub(r"\s+", " ", text).strip()

        if len(text) > 200:
            return text[:MAX_PAGE_CHARS]

        # -----------------------------------------
        # Method 3: BeautifulSoup fallback
        # -----------------------------------------

        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "header",
                "footer",
                "nav",
                "aside",
            ]
        ):
            tag.decompose()

        text = soup.get_text(
            separator=" ",
            strip=True,
        )

        text = re.sub(r"\s+", " ", text).strip()

        if not text:
            return "Could not extract readable content from this URL."

        return text[:MAX_PAGE_CHARS]

    except requests.exceptions.Timeout:
        return "Failed to scrape URL: request timed out."

    except requests.exceptions.HTTPError as e:
        return f"Failed to scrape URL: HTTP error - {e}"

    except requests.exceptions.RequestException as e:
        return f"Failed to scrape URL: request error - {e}"

    except Exception as e:
        return f"Failed to scrape URL: {str(e)}"