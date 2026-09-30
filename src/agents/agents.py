from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from src.tools.tools import web_search, scrape_url


load_dotenv()


# ============================================================
# LLM
# ============================================================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)


# ============================================================
# SEARCH AGENT
# ============================================================

def build_search_agent():

    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt="""
You are a web research agent.

Your job is to search the web for information.

IMPORTANT:
When using the web_search tool, you MUST provide
exactly one argument:

query

Example:

web_search({
    "query": "AI job market 2026"
})

Never call web_search with cursor, id, page,
or any other parameter.

Call web_search at most 2 times.
After the first 2 searches, write your final answer.

After searching, summarize the useful results
and include the URLs.
""",
    )


# ============================================================
# READER AGENT
# ============================================================

def build_reader_agent():

    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt="""
You are a web reading agent.

Your job is to read a URL and extract useful
information from it.

IMPORTANT:
When using the scrape_url tool, you MUST provide
exactly one argument:

url

Example:

scrape_url({
    "url": "https://example.com"
})

Never provide cursor, id, query, or any other parameter.

Call scrape_url exactly once, for the single best URL.
After scraping, summarize the important information.
""",
    )


# ============================================================
# WRITER
# ============================================================

writer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert research writer.

Write clear, structured, factual and insightful
research reports.

Use only the research provided to you.
Do not invent facts.
""",
        ),
        (
            "human",
            """
Write a detailed research report on:

Topic:
{topic}

Research:
{research}

Use this structure:

1. Introduction

2. Key Findings
   - At least 3 detailed points

3. Conclusion

4. Sources
   - Include URLs available in the research

Be factual, clear and professional.
""",
        ),
    ]
)

writer_chain = writer_prompt | llm | StrOutputParser()


# ============================================================
# CRITIC
# ============================================================

critic_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a research critic.

Analyze the report carefully for:
- factual accuracy
- completeness
- clarity
- structure
- evidence
- sources
- unsupported claims
""",
        ),
        (
            "human",
            """
Review this research report:

{report}

Respond using:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
...
""",
        ),
    ]
)

critic_chain = critic_prompt | llm | StrOutputParser()