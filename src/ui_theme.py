"""Shared visual theme and UI components for DocuMind AI — professional dark mode."""

from __future__ import annotations

import streamlit as st

THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --dm-bg: #0a0e17;
        --dm-surface: #131a2b;
        --dm-surface-2: #1a2332;
        --dm-border: #2a3548;
        --dm-border-light: #3d4f6f;
        --dm-text: #e8edf5;
        --dm-text-muted: #8b9cb3;
        --dm-accent: #3b82f6;
        --dm-accent-glow: rgba(59, 130, 246, 0.35);
        --dm-success: #22c55e;
        --dm-success-dim: rgba(34, 197, 94, 0.12);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    .stApp {
        background: var(--dm-bg);
        background-image:
            radial-gradient(ellipse 80% 50% at 50% -20%, rgba(59, 130, 246, 0.08), transparent),
            radial-gradient(ellipse 60% 40% at 100% 0%, rgba(99, 102, 241, 0.05), transparent);
    }

    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2rem;
        max-width: 1180px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1220 0%, #0a0e17 100%);
        border-right: 1px solid var(--dm-border);
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: var(--dm-text) !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: var(--dm-border);
    }

    /* Hero */
    .dm-hero {
        background: linear-gradient(135deg, #0d1526 0%, #152238 40%, #1a3055 100%);
        border: 1px solid var(--dm-border-light);
        border-radius: 14px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.25rem;
        color: var(--dm-text);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.04);
        position: relative;
        overflow: hidden;
    }
    .dm-hero::before {
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 40%; height: 100%;
        background: radial-gradient(circle at 80% 20%, var(--dm-accent-glow), transparent 70%);
        pointer-events: none;
    }
    .dm-hero-title {
        font-size: 1.85rem;
        font-weight: 700;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.03em;
        color: #ffffff;
        position: relative;
    }
    .dm-hero-sub {
        font-size: 0.98rem;
        color: var(--dm-text-muted);
        margin: 0;
        line-height: 1.5;
        position: relative;
    }
    .dm-badge {
        display: inline-block;
        background: rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.35);
        color: #93c5fd;
        border-radius: 6px;
        padding: 0.2rem 0.65rem;
        font-size: 0.72rem;
        font-weight: 600;
        margin-bottom: 0.7rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        position: relative;
    }

    /* Step cards */
    .dm-step {
        background: var(--dm-surface);
        border: 1px solid var(--dm-border);
        border-radius: 10px;
        padding: 1rem 1.15rem;
        min-height: 128px;
    }
    .dm-step-done {
        border-color: rgba(34, 197, 94, 0.4);
        background: linear-gradient(135deg, var(--dm-success-dim) 0%, var(--dm-surface) 100%);
        box-shadow: 0 0 20px rgba(34, 197, 94, 0.08);
    }
    .dm-step-pending {
        border-left: 3px solid var(--dm-border-light);
    }
    .dm-step-active {
        border-left: 3px solid var(--dm-accent);
        box-shadow: 0 0 24px var(--dm-accent-glow);
        background: var(--dm-surface-2);
    }
    .dm-step-num {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--dm-accent);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .dm-step-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--dm-text);
        margin: 0.4rem 0 0.25rem;
    }
    .dm-step-desc {
        font-size: 0.82rem;
        color: var(--dm-text-muted);
        line-height: 1.45;
        margin: 0;
    }
    .dm-step-status {
        font-size: 0.78rem;
        font-weight: 600;
        margin-top: 0.6rem;
        color: var(--dm-text-muted);
    }
    .dm-step-status.done { color: var(--dm-success); }

    /* Agent chips */
    .dm-agent-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
        gap: 0.55rem;
    }
    .dm-agent-chip {
        background: var(--dm-surface-2);
        border: 1px solid var(--dm-border);
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
    }
    .dm-agent-chip strong {
        display: block;
        font-size: 0.8rem;
        color: var(--dm-text);
        font-weight: 600;
    }
    .dm-agent-chip span {
        font-size: 0.72rem;
        color: var(--dm-text-muted);
        line-height: 1.35;
    }

    /* Sidebar brand */
    .dm-sidebar-brand {
        text-align: left;
        padding: 0.25rem 0 0.5rem;
    }
    .dm-sidebar-brand .dm-logo {
        font-size: 1.15rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .dm-sidebar-brand .dm-logo span {
        color: var(--dm-accent);
    }
    .dm-sidebar-brand p {
        margin: 0.2rem 0 0;
        font-size: 0.75rem;
        color: var(--dm-text-muted);
    }

    /* Progress */
    .dm-progress-item {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        padding: 0.3rem 0;
        font-size: 0.84rem;
        color: var(--dm-text-muted);
    }
    .dm-progress-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .dm-progress-dot.done {
        background: var(--dm-success);
        box-shadow: 0 0 8px rgba(34, 197, 94, 0.5);
    }
    .dm-progress-dot.pending {
        background: var(--dm-border-light);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: transparent;
        border-bottom: 1px solid var(--dm-border);
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        padding: 0 1.1rem;
        font-weight: 500;
        font-size: 0.9rem;
        color: var(--dm-text-muted) !important;
        background: transparent !important;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected="true"] {
        color: #93c5fd !important;
        background: var(--dm-surface) !important;
        border-bottom: 2px solid var(--dm-accent) !important;
    }

    /* Bordered containers — separated panels */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--dm-surface);
        border-color: var(--dm-border) !important;
        border-radius: 12px;
        padding: 1.35rem 1.5rem !important;
        margin-bottom: 1.75rem !important;
    }

    /* Tab content breathing room */
    .stTabs [data-testid="stVerticalBlock"] {
        padding-top: 1.5rem;
        gap: 1.25rem;
    }

    /* Column gaps — prevent cards touching */
    [data-testid="column"] {
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 1rem !important;
        margin-bottom: 0.5rem;
    }

    /* Vertical spacing between widgets */
    [data-testid="stVerticalBlock"] > div {
        gap: 0.85rem;
    }

    /* Section headers */
    .dm-section-header {
        margin: 0 0 1rem 0;
        padding-bottom: 0.65rem;
        border-bottom: 1px solid var(--dm-border);
    }
    .dm-section-header h5 {
        margin: 0;
        font-size: 1rem;
        font-weight: 600;
        color: var(--dm-text);
    }
    .dm-section-header p {
        margin: 0.25rem 0 0;
        font-size: 0.82rem;
        color: var(--dm-text-muted);
    }

    /* Explicit spacers */
    .dm-spacer-sm { height: 0.75rem; display: block; }
    .dm-spacer-md { height: 1.5rem; display: block; }
    .dm-spacer-lg { height: 2.25rem; display: block; }

    /* Step cards row */
    .dm-steps-row {
        margin-bottom: 0.5rem;
    }

    /* Expanders — never stacked flush */
    [data-testid="stExpander"] {
        margin-bottom: 1rem !important;
    }
    [data-testid="stExpander"] + [data-testid="stExpander"] {
        margin-top: 0.25rem;
    }

    /* Alerts — space from neighbours */
    [data-testid="stAlert"] {
        margin: 1rem 0 !important;
    }

    /* Dividers — more margin */
    hr {
        border-color: var(--dm-border);
        opacity: 0.5;
        margin: 2rem 0 !important;
    }

    /* Radio groups — padded */
    .stRadio > div {
        gap: 0.75rem;
        padding: 0.5rem 0 1rem;
    }

    /* Selectbox — bottom margin */
    .stSelectbox {
        margin-bottom: 0.75rem;
    }

    /* Metrics row gap */
    [data-testid="stMetric"] {
        margin-bottom: 0.5rem;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        border: 1px solid rgba(59, 130, 246, 0.5);
        border-radius: 8px;
        font-weight: 600;
        color: #ffffff;
        box-shadow: 0 4px 16px var(--dm-accent-glow);
        transition: all 0.15s ease;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        box-shadow: 0 6px 20px var(--dm-accent-glow);
        border-color: #60a5fa;
    }
    .stButton > button[kind="secondary"] {
        background: var(--dm-surface-2);
        border: 1px solid var(--dm-border);
        color: var(--dm-text);
        border-radius: 8px;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: var(--dm-border-light);
        background: #1f2a3d;
    }

    /* Inputs */
    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
        background: var(--dm-surface-2) !important;
        border-color: var(--dm-border) !important;
        color: var(--dm-text) !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--dm-accent) !important;
        box-shadow: 0 0 0 2px var(--dm-accent-glow) !important;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background: var(--dm-surface);
        border: 1px solid var(--dm-border);
        border-radius: 10px;
        padding: 0.7rem 1rem;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        color: var(--dm-text-muted) !important;
        font-weight: 500 !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--dm-text) !important;
        font-weight: 700 !important;
    }

    /* Headings in main area */
    .main h1, .main h2, .main h3, .main h4, .main h5 {
        color: var(--dm-text);
    }
    .main p, .main li, .main span {
        color: var(--dm-text);
    }
    .main .stCaption, [data-testid="stCaptionContainer"] {
        color: var(--dm-text-muted) !important;
    }

    /* Alerts */
    [data-testid="stAlert"] {
        border-radius: 8px;
        border: 1px solid var(--dm-border);
    }

    /* Expander */
    [data-testid="stExpander"] {
        background: var(--dm-surface);
        border: 1px solid var(--dm-border);
        border-radius: 8px;
        margin-bottom: 1rem !important;
    }
    [data-testid="stExpander"] summary {
        color: var(--dm-text) !important;
        font-weight: 500;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--dm-border);
        border-radius: 8px;
        overflow: hidden;
    }

    /* Radio */
    .stRadio > label {
        color: var(--dm-text-muted) !important;
        font-weight: 500;
    }

    /* Chat */
    [data-testid="stChatMessage"] {
        background: var(--dm-surface);
        border: 1px solid var(--dm-border);
        border-radius: 10px;
    }

    /* Progress bar */
    .stProgress > div > div {
        background: var(--dm-accent);
    }

    /* Download button */
    .stDownloadButton > button {
        background: var(--dm-surface-2);
        border: 1px solid var(--dm-border);
        color: var(--dm-text);
        border-radius: 8px;
    }

    footer, #MainMenu { visibility: hidden; }
    header[data-testid="stHeader"] {
        background: transparent;
    }
</style>
"""


def inject_theme() -> None:
    """Inject global dark CSS theme."""
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def render_hero_header(title: str = "DocuMind AI", subtitle: str = "", badge: str = "v6.0") -> None:
    """Render the main hero banner."""
    if title == "DocuMind AI":
        title_html = 'Docu<span style="color:#3b82f6">Mind</span> AI'
    else:
        title_html = title

    st.markdown(
        f"""
        <div class="dm-hero">
            <div class="dm-badge">{badge}</div>
            <div class="dm-hero-title">{title_html}</div>
            <p class="dm-hero-sub">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section(title: str, description: str = "") -> None:
    """Open a styled section with title."""
    desc_html = f'<p class="dm-section-desc">{description}</p>' if description else ""
    st.markdown(
        f"""
        <div style="background:#131a2b;border:1px solid #2a3548;border-radius:10px;
        padding:1.1rem 1.3rem;margin-bottom:0.75rem;">
            <div style="font-size:1.05rem;font-weight:600;color:#e8edf5;margin:0;">{title}</div>
            {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_step_card(
    step_num: int,
    title: str,
    description: str,
    done: bool,
    active: bool = False,
) -> None:
    """Render a workflow step card."""
    if done:
        state_class = "dm-step-done"
        status = "Concluído"
        status_class = "done"
    elif active:
        state_class = "dm-step-active"
        status = "Em progresso"
        status_class = ""
    else:
        state_class = "dm-step-pending"
        status = "Por fazer"
        status_class = ""

    st.markdown(
        f"""
        <div class="dm-step {state_class}">
            <div class="dm-step-num">Passo {step_num}</div>
            <div class="dm-step-title">{title}</div>
            <p class="dm-step-desc">{description}</p>
            <div class="dm-step-status {status_class}">{status}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    """Sidebar logo / brand block."""
    st.sidebar.markdown(
        """
        <div class="dm-sidebar-brand">
            <p class="dm-logo">Docu<span>Mind</span> AI</p>
            <p>Tech Analyst Assistant</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_progress_item(label: str, done: bool) -> None:
    """Single progress line for sidebar."""
    dot_class = "done" if done else "pending"
    st.sidebar.markdown(
        f"""
        <div class="dm-progress-item">
            <div class="dm-progress-dot {dot_class}"></div>
            <span>{label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_agent_chips(agents: list[tuple[str, str]]) -> None:
    """Render agent name + description chips."""
    chips = "".join(
        f'<div class="dm-agent-chip"><strong>{name}</strong><span>{desc}</span></div>'
        for name, desc in agents
    )
    st.markdown(f'<div class="dm-agent-grid">{chips}</div>', unsafe_allow_html=True)


def render_panel_header(title: str, description: str = "") -> None:
    """Render a separated section header above a panel."""
    desc = f"<p>{description}</p>" if description else ""
    st.markdown(
        f'<div class="dm-section-header"><h5>{title}</h5>{desc}</div>',
        unsafe_allow_html=True,
    )


def spacer(size: str = "md") -> None:
    """Add vertical space between sections."""
    st.markdown(f'<div class="dm-spacer-{size}"></div>', unsafe_allow_html=True)


def panel(title: str = "", description: str = ""):
    """Context manager: header + bordered panel with padding."""
    from contextlib import contextmanager

    @contextmanager
    def _panel():
        if title:
            render_panel_header(title, description)
        with st.container(border=True):
            yield
        spacer("md")

    return _panel()


def mode_selector_container():
    """Context manager wrapper using st.container with border."""
    return st.container(border=True)
