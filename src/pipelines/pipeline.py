from langgraph.errors import GraphRecursionError

from src.agents.agents import (
    build_search_agent,
    build_reader_agent,
    writer_chain,
    critic_chain,
)


def run_agent(agent, prompt: str, recursion_limit: int) -> str:
    summary = ""
    tool_output = ""

    try:
        for chunk in agent.stream(
            {"messages": [("user", prompt)]},
            config={"recursion_limit": recursion_limit},
        ):
            for update in chunk.values():
                if not isinstance(update, dict):
                    continue

                for message in update.get("messages") or []:
                    content = message.content or ""

                    if getattr(message, "type", None) == "tool" and content:
                        tool_output = content

                    if getattr(message, "type", None) == "ai" and content.strip():
                        summary = content

    except GraphRecursionError:
        print("\nAgent hit the step limit, using the best answer so far.\n")

    if summary:
        return summary

    return tool_output or "The agent stopped before writing a summary."


def run_research_pipeline(topic: str, progress_cb=None) -> dict:
    """
    progress_cb(stage, state) is optional. It is called with:
      stage: "search" | "read" | "write" | "critique"
      state: "start" | "done"
    The Streamlit UI uses it to turn each step green as it finishes.
    """
    cb = progress_cb or (lambda stage, state="start": None)

    state = {}

    # ========================================================
    # STEP 1 — SEARCH
    # ========================================================

    print("\n" + "=" * 60)
    print("STEP 1 - SEARCH AGENT")
    print("=" * 60)

    cb("search", "start")

    search_agent = build_search_agent()

    state["search_results"] = run_agent(
        search_agent,
        f"""
Find recent, reliable and detailed information about:

{topic}

Search the web and provide the most relevant sources.

Keep your response concise.
Return the important findings and URLs.
""",
        recursion_limit=8,
    )

    cb("search", "done")

    print("\nSearch Result:\n")
    print(state["search_results"])

    # ========================================================
    # STEP 2 — READER
    # ========================================================

    print("\n" + "=" * 60)
    print("STEP 2 - READER AGENT")
    print("=" * 60)

    cb("read", "start")

    reader_agent = build_reader_agent()

    # IMPORTANT:
    # Limit the search result sent to the reader.
    search_context = state["search_results"][:4000]

    reader_result = run_agent(
        reader_agent,
        f"""
We are researching:

"{topic}"

Below are search results:

{search_context}

Choose ONE of the most relevant URLs from the search results
and scrape that URL.

Return a detailed summary of the information you extracted.
""",
        recursion_limit=6,
    )

    state["scraped_content"] = reader_result

    cb("read", "done")

    print("\nScraped Content:\n")
    print(state["scraped_content"])

    # ========================================================
    # STEP 3 — WRITER
    # ========================================================

    print("\n" + "=" * 60)
    print("STEP 3 - WRITER")
    print("=" * 60)

    cb("write", "start")

    # Limit research to avoid another oversized request.
    research_combined = f"""
SEARCH RESULTS:

{state["search_results"][:3000]}

DETAILED SCRAPED CONTENT:

{state["scraped_content"][:5000]}
"""

    state["report"] = writer_chain.invoke(
        {
            "topic": topic,
            "research": research_combined,
        }
    )

    cb("write", "done")

    print("\nFinal Report:\n")
    print(state["report"])

    # ========================================================
    # STEP 4 — CRITIC
    # ========================================================

    print("\n" + "=" * 60)
    print("STEP 4 - CRITIC")
    print("=" * 60)

    cb("critique", "start")

    # Limit report size before sending to critic.
    report_for_critic = state["report"][:6000]

    state["feedback"] = critic_chain.invoke(
        {
            "report": report_for_critic,
        }
    )

    cb("critique", "done")

    print("\nCritic Report:\n")
    print(state["feedback"])

    # ========================================================
    # RETURN STATE
    # ========================================================

    return state