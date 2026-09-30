import importlib
import inspect
import time

import streamlit as st

from src.pipelines.pipeline import run_research_pipeline

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# STYLE
# Palette: ink #0F1419 · panel #151B23 · raised #1B232D · line #263241
#          text #E4E8EE · muted #8E9BAC · amber #E3B25A · teal #6DB6C8
# Type:    Newsreader (headlines + report), Instrument Sans (interface)
# ============================================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600&family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&display=swap');

:root {
    --ink: #0F1419;
    --panel: #151B23;
    --raised: #1B232D;
    --line: #263241;
    --text: #E4E8EE;
    --muted: #8E9BAC;
    --amber: #E3B25A;
    --teal: #6DB6C8;
    --green: #4CC38A;
    --red: #E5646A;
}

html, body, [class*="css"], .stMarkdown, button, input, textarea, label {
    font-family: 'Instrument Sans', system-ui, sans-serif;
}

.block-container { padding-top: 2.6rem; padding-bottom: 4rem; max-width: 1040px; }
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }

/* ---------- Hero ---------- */
.hero-title {
    font-family: 'Newsreader', Georgia, serif;
    font-weight: 500;
    font-size: 3rem;
    line-height: 1.05;
    letter-spacing: -0.02em;
    color: var(--text);
    margin: 0 0 .7rem 0;
}
.hero-sub {
    color: var(--muted);
    font-size: 1.08rem;
    line-height: 1.55;
    max-width: 52ch;
    margin: 0 0 1.6rem 0;
}

/* Live pipeline tracker */
.steps { display: flex; align-items: center; gap: .6rem; margin-bottom: 2rem; flex-wrap: wrap; }
.step { display: flex; align-items: center; gap: .55rem; color: var(--muted); font-size: .93rem; font-weight: 500; transition: color .2s; }
.step i {
    font-style: normal;
    width: 1.6rem; height: 1.6rem;
    display: inline-flex; align-items: center; justify-content: center;
    border: 1px solid var(--line);
    color: var(--muted);
    border-radius: 50%;
    font-size: .78rem; font-weight: 600;
    transition: all .25s;
}
.step-line { width: 2.2rem; height: 1px; background: var(--line); transition: background .25s; }
.step-line.done { background: var(--green); }

.step.active { color: var(--text); }
.step.active i { border-color: var(--amber); color: var(--amber); animation: pulse 1.3s ease-in-out infinite; }

.step.done { color: var(--text); }
.step.done i { background: var(--green); border-color: var(--green); color: #07150E; }

.step.error { color: var(--text); }
.step.error i { border-color: var(--red); color: var(--red); }

@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(227,178,90,.45); }
    50%      { box-shadow: 0 0 0 7px rgba(227,178,90,0); }
}

/* ---------- Inputs ---------- */
.stTextInput input {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 10px;
    color: var(--text);
    padding: .85rem 1rem;
    font-size: 1.02rem;
}
.stTextInput input:focus { border-color: var(--amber); box-shadow: 0 0 0 1px var(--amber); }
.stTextInput input::placeholder { color: #5E6B7B; }

.stButton > button {
    border-radius: 10px;
    font-weight: 500;
    transition: border-color .15s, background .15s;
}
.stButton > button[kind="secondary"] {
    background: transparent;
    border: 1px solid var(--line);
    color: var(--muted);
    font-size: .84rem;
    padding: .4rem .7rem;
}
.stButton > button[kind="secondary"]:hover { border-color: var(--teal); color: var(--teal); background: transparent; }
.stButton > button[kind="primary"] {
    background: var(--amber);
    color: #1A1405;
    border: none;
    font-weight: 600;
    font-size: 1rem;
    padding: .7rem 1rem;
}
.stButton > button[kind="primary"]:hover { background: #EDC275; color: #1A1405; }

/* ---------- Results ---------- */
.result-title {
    font-family: 'Newsreader', Georgia, serif;
    font-size: 1.7rem;
    font-weight: 500;
    color: var(--text);
    margin: 2.4rem 0 1rem 0;
    line-height: 1.2;
}

.facts { display: flex; margin-bottom: 1.8rem; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.fact { flex: 1; padding: 1rem 1.2rem; border-right: 1px solid var(--line); }
.fact:last-child { border-right: none; }
.fact b { font-family: 'Newsreader', Georgia, serif; font-size: 1.7rem; font-weight: 500; color: var(--text); display: block; line-height: 1.1; }
.fact span { color: var(--muted); font-size: .85rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 1.4rem; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { padding: .6rem 0; font-weight: 500; color: var(--muted); background: transparent; }
.stTabs [aria-selected="true"] { color: var(--text); }
.stTabs [data-baseweb="tab-highlight"] { background: var(--amber); height: 2px; }

/* Report card: serif, comfortable measure */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] {
    font-family: 'Newsreader', Georgia, serif;
    font-size: 1.14rem;
    line-height: 1.75;
    max-width: 70ch;
}
[data-testid="stVerticalBlockBorderWrapper"] h1,
[data-testid="stVerticalBlockBorderWrapper"] h2,
[data-testid="stVerticalBlockBorderWrapper"] h3 {
    font-family: 'Newsreader', Georgia, serif;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: var(--text);
    margin-top: 1.6rem;
}
[data-testid="stVerticalBlockBorderWrapper"] h1 { font-size: 1.9rem; }
[data-testid="stVerticalBlockBorderWrapper"] h2 { font-size: 1.5rem; }
[data-testid="stVerticalBlockBorderWrapper"] h3 { font-size: 1.2rem; }
[data-testid="stVerticalBlockBorderWrapper"] a { color: var(--teal); }
[data-testid="stVerticalBlockBorderWrapper"] blockquote { border-left: 2px solid var(--amber); color: var(--muted); }

/* Expanders + status */
details { background: var(--panel); border: 1px solid var(--line) !important; border-radius: 12px !important; }
details summary { font-weight: 500; }

.stDownloadButton > button {
    background: transparent;
    border: 1px solid var(--line);
    color: var(--text);
    border-radius: 10px;
    margin-bottom: .8rem;
}
.stDownloadButton > button:hover { border-color: var(--amber); color: var(--amber); }

/* Sidebar */
[data-testid="stSidebar"] { border-right: 1px solid var(--line); }
[data-testid="stSidebar"] h3 { font-family: 'Newsreader', Georgia, serif; font-weight: 500; font-size: 1.35rem; }
.side-step { margin-bottom: 1rem; }
.side-step b { display: block; color: var(--text); font-weight: 600; font-size: .95rem; }
.side-step span { color: var(--muted); font-size: .88rem; line-height: 1.45; }

@media (max-width: 720px) {
    .hero-title { font-size: 2.2rem; }
    .facts { flex-direction: column; }
    .fact { border-right: none; border-bottom: 1px solid var(--line); }
    .fact:last-child { border-bottom: none; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# STATE
# ============================================================

st.session_state.setdefault("topic", "")
st.session_state.setdefault("result", None)
st.session_state.setdefault("elapsed", 0.0)
st.session_state.setdefault("ran_topic", "")

STAGES = [("search", "Search"), ("read", "Read"), ("write", "Write"), ("critique", "Critique")]
st.session_state.setdefault("stages", {k: "idle" for k, _ in STAGES})

EXAMPLES = [
    "Impact of AI on the job market in 2026",
    "State of open-source LLMs",
    "RAG vs fine-tuning",
]


def set_topic(value: str) -> None:
    st.session_state.topic = value


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.subheader("How it works")
    for name, desc in [
        ("Search agent", "Finds relevant sources on the web."),
        ("Reader agent", "Opens the best pages and pulls out the content."),
        ("Writer", "Drafts a structured report from what was read."),
        ("Critic", "Reviews the draft and flags weak spots."),
    ]:
        st.markdown(
            f'<div class="side-step"><b>{name}</b><span>{desc}</span></div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.caption("Built with LangChain, Groq, Tavily and Streamlit")

    if st.session_state.result and st.button("Clear results", use_container_width=True):
        st.session_state.result = None
        st.session_state.stages = {k: "idle" for k, _ in STAGES}
        st.rerun()

# ============================================================
# HERO
# ============================================================

st.markdown(
    """
<div class="hero-title">Ask a question.<br>Get a sourced report.</div>
<p class="hero-sub">Four agents search the web, read the pages, write the report and critique it, so you can see where it is weak.</p>
""",
    unsafe_allow_html=True,
)

# ============================================================
# LIVE TRACKER
# ============================================================


def render_tracker(slot) -> None:
    states = st.session_state.stages
    parts = []
    for idx, (key, label) in enumerate(STAGES):
        state = states[key]
        mark = "✓" if state == "done" else ("!" if state == "error" else str(idx + 1))
        parts.append(f'<div class="step {state}"><i>{mark}</i>{label}</div>')
        if idx < len(STAGES) - 1:
            parts.append(f'<div class="step-line {"done" if state == "done" else ""}"></div>')
    slot.markdown('<div class="steps">' + "".join(parts) + "</div>", unsafe_allow_html=True)


tracker = st.empty()
render_tracker(tracker)

# ============================================================
# INPUT
# ============================================================

st.text_input(
    "Research topic",
    key="topic",
    placeholder="What do you want to research?",
    label_visibility="collapsed",
)

cols = st.columns(len(EXAMPLES))
for col, example in zip(cols, EXAMPLES):
    col.button(
        example,
        key=f"ex_{example}",
        on_click=set_topic,
        args=(example,),
        use_container_width=True,
    )

run = st.button("Start research", type="primary", use_container_width=True)

# ============================================================
# RUN PIPELINE
# ============================================================

if run:
    topic = st.session_state.topic.strip()

    if not topic:
        st.warning("Enter a research topic to get started.")
        st.stop()

    st.session_state.stages = {k: "idle" for k, _ in STAGES}
    render_tracker(tracker)

    def on_progress(stage: str, state: str = "start") -> None:
        """Called by the pipeline: on_progress("search", "start") / on_progress("search", "done")."""
        if stage in st.session_state.stages:
            st.session_state.stages[stage] = "done" if state == "done" else "active"
            render_tracker(tracker)

    # Always use the latest pipeline.py (Streamlit can keep a stale copy in memory).
    import src.pipelines.pipeline as pipeline_module
    run_research_pipeline = importlib.reload(pipeline_module).run_research_pipeline

    supports_progress = "progress_cb" in inspect.signature(run_research_pipeline).parameters
    started = time.time()

    try:
        with st.spinner("Researching. This usually takes a minute or two."):
            if supports_progress:
                result = run_research_pipeline(topic, progress_cb=on_progress)
            else:
                # Pipeline can't report stages yet: show everything as running.
                st.warning(
                    "Your pipeline.py doesn't accept `progress_cb`, so steps can't turn green one by one. "
                    "Update src/pipelines/pipeline.py and restart Streamlit."
                )
                for key, _ in STAGES:
                    st.session_state.stages[key] = "active"
                render_tracker(tracker)
                result = run_research_pipeline(topic)

        for key, _ in STAGES:
            st.session_state.stages[key] = "done"
        render_tracker(tracker)

        st.session_state.result = result
        st.session_state.elapsed = time.time() - started
        st.session_state.ran_topic = topic

    except Exception as e:
        for key, _ in STAGES:
            if st.session_state.stages[key] == "active":
                st.session_state.stages[key] = "error"
        render_tracker(tracker)
        st.error(f"The pipeline stopped with an error: {e}")
        st.stop()

# ============================================================
# RESULTS
# ============================================================

result = st.session_state.result

if result:
    report = result.get("report", "")
    feedback = result.get("feedback", "")
    search_results = result.get("search_results", "")
    scraped = result.get("scraped_content", "")

    st.markdown(
        f'<div class="result-title">{st.session_state.ran_topic}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="facts">
  <div class="fact"><b>{len(report.split()):,}</b><span>words in the report</span></div>
  <div class="fact"><b>{st.session_state.elapsed:.0f}s</b><span>total time</span></div>
  <div class="fact"><b>{len(scraped.split()):,}</b><span>words read from sources</span></div>
</div>
""",
        unsafe_allow_html=True,
    )

    tab_report, tab_critic, tab_sources = st.tabs(["Report", "Critic feedback", "Sources"])

    with tab_report:
        if report:
            st.download_button(
                "Download as Markdown",
                data=report,
                file_name="research_report.md",
                mime="text/markdown",
            )
            with st.container(border=True):
                st.markdown(report)
        else:
            st.warning("No report was generated.")

    with tab_critic:
        if feedback:
            with st.container(border=True):
                st.markdown(feedback)
        else:
            st.warning("No critic feedback was generated.")

    with tab_sources:
        with st.expander("Search results"):
            st.markdown(search_results or "No search results.")
        with st.expander("Scraped content"):
            st.markdown(scraped or "No scraped content.")