"""
streamlit_app.py
================
Streamlit Chat UI for the Text-to-SQL pipeline.

Run with:
    streamlit run streamlit_app.py
"""

import json
import pandas as pd
import streamlit as st

from database import test_connection
from executor import run_pipeline

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Text-to-SQL Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Dark gradient background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: #e8e8f0;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(255,255,255,0.05);
        border-right: 1px solid rgba(255,255,255,0.1);
    }

    /* Chat messages */
    .chat-bubble-user {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 18px 18px 4px 18px;
        padding: 12px 18px;
        margin: 8px 0;
        max-width: 80%;
        float: right;
        clear: both;
        color: white;
        font-size: 0.95rem;
        box-shadow: 0 4px 15px rgba(102,126,234,0.4);
    }
    .chat-bubble-assistant {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 18px 18px 18px 4px;
        padding: 12px 18px;
        margin: 8px 0;
        max-width: 85%;
        float: left;
        clear: both;
        color: #e8e8f0;
        font-size: 0.9rem;
        backdrop-filter: blur(10px);
    }

    /* Status badges */
    .badge-success { background:#10b981; color:white; padding:3px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; }
    .badge-failed  { background:#ef4444; color:white; padding:3px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; }
    .badge-blocked { background:#f59e0b; color:white; padding:3px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; }
    .badge-retry   { background:#8b5cf6; color:white; padding:3px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; }

    /* Code blocks */
    .sql-block {
        background: rgba(0,0,0,0.4);
        border: 1px solid rgba(102,126,234,0.4);
        border-radius: 10px;
        padding: 14px;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        color: #a5f3fc;
        white-space: pre-wrap;
        margin: 8px 0;
    }

    /* Stat cards */
    .stat-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        backdrop-filter: blur(5px);
    }
    .stat-number { font-size: 2rem; font-weight: 700; color: #a78bfa; }
    .stat-label  { font-size: 0.75rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; }

    /* Input box */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(102,126,234,0.5) !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 12px 16px !important;
    }

    /* Divider */
    hr { border-color: rgba(255,255,255,0.1); }

    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.05) !important;
        border-radius: 8px !important;
        color: #a5b4fc !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── State init ────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "run_count" not in st.session_state:
    st.session_state.run_count = 0
if "success_count" not in st.session_state:
    st.session_state.success_count = 0
if "retry_count" not in st.session_state:
    st.session_state.retry_count = 0


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 Text-to-SQL")
    st.markdown("*Powered by OpenRouter + PostgreSQL*")
    st.divider()

    # DB status
    db_ok = test_connection()
    if db_ok:
        st.success("✅ Database connected")
    else:
        st.error("❌ Database offline")
        st.caption("Start with: `docker compose up -d`")

    st.divider()

    # Session stats
    st.markdown("### 📊 Session Stats")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{st.session_state.run_count}</div>'
            f'<div class="stat-label">Queries</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{st.session_state.success_count}</div>'
            f'<div class="stat-label">Success</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{st.session_state.retry_count}</div>'
            f'<div class="stat-label">Retried</div></div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # Example questions
    st.markdown("### 💡 Try these")
    examples = [
        "How many customers are from the USA?",
        "Show all orders placed by customers in Germany",
        "Which products have stock less than 100?",
        "Find total payments by each customer",
        "Top 5 customers by order count",
        "List all employees and their office city",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex[:20]}", use_container_width=True):
            st.session_state["prefill"] = ex

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.run_count = 0
        st.session_state.success_count = 0
        st.session_state.retry_count = 0
        st.rerun()


# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='text-align:center; background: linear-gradient(90deg,#667eea,#a78bfa); "
    "-webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:4px;'>"
    "🧠 Text-to-SQL Assistant</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center; color:#9ca3af; margin-bottom:24px;'>"
    "Ask a question in plain English — get SQL + results instantly</p>",
    unsafe_allow_html=True,
)


# ── Render chat history ───────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🤖"):
            _render = msg.get("render")
            if _render:
                # Status badge
                status = _render["status"]
                badge_class = {
                    "success": "badge-success",
                    "failed": "badge-failed",
                    "blocked": "badge-blocked",
                    "error": "badge-failed",
                }.get(status, "badge-blocked")
                retry_html = (
                    ' &nbsp;<span class="badge-retry">🔄 Retried</span>'
                    if _render.get("retried")
                    else ""
                )
                st.markdown(
                    f'<span class="{badge_class}">{status.upper()}</span>'
                    f'{retry_html} &nbsp; <small style="color:#9ca3af">{_render["latency_ms"]:.0f} ms</small>',
                    unsafe_allow_html=True,
                )

                # SQL
                if _render.get("sql"):
                    with st.expander("📝 Generated SQL", expanded=True):
                        st.code(_render["sql"], language="sql")

                if _render.get("fixed_sql"):
                    with st.expander("🔧 Fixed SQL (after retry)"):
                        st.code(_render["fixed_sql"], language="sql")

                # Decomposition
                if _render.get("decomposition"):
                    with st.expander("🔬 Query Decomposition"):
                        st.json(_render["decomposition"])

                # Results table
                if _render.get("rows"):
                    st.markdown(f"**{_render['row_count']} row(s) returned:**")
                    df = pd.DataFrame(_render["rows"])
                    st.dataframe(
                        df, use_container_width=True, height=min(300, 40 + 35 * len(df))
                    )
                elif status == "success":
                    st.info("Query executed successfully — no rows returned.")

                # Error
                if _render.get("error"):
                    st.error(f"⚠️ {_render['error']}")
            else:
                st.write(msg["content"])


# ── Chat input ────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("prefill", "")
question = (
    st.chat_input(
        "Ask anything about the Classic Models database…",
        key="chat_input",
    )
    or prefill
)

if question:
    # Add user bubble
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="👤"):
        st.write(question)

    # Run pipeline
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🔄 Thinking… (Decompose → Generate → Execute)"):
            result = run_pipeline(question)

        # Update session stats
        st.session_state.run_count += 1
        if result["status"] == "success":
            st.session_state.success_count += 1
        if result["retry_attempted"]:
            st.session_state.retry_count += 1

        render_data = {
            "status": result["status"],
            "sql": result.get("sql"),
            "fixed_sql": result.get("fixed_sql"),
            "decomposition": result.get("decomposition"),
            "rows": (result.get("result") or {}).get("rows", []),
            "row_count": (result.get("result") or {}).get("row_count", 0),
            "error": result.get("error"),
            "latency_ms": result["latency_ms"],
            "retried": result["retry_attempted"],
        }

        # Status badge
        status = result["status"]
        badge_class = {
            "success": "badge-success",
            "failed": "badge-failed",
            "blocked": "badge-blocked",
            "error": "badge-failed",
        }.get(status, "badge-blocked")
        retry_html = (
            ' &nbsp;<span class="badge-retry">🔄 Retried</span>'
            if result["retry_attempted"]
            else ""
        )
        st.markdown(
            f'<span class="{badge_class}">{status.upper()}</span>'
            f'{retry_html} &nbsp; <small style="color:#9ca3af">{result["latency_ms"]:.0f} ms</small>',
            unsafe_allow_html=True,
        )

        if result.get("sql"):
            with st.expander("📝 Generated SQL", expanded=True):
                st.code(result["sql"], language="sql")

        if result.get("fixed_sql"):
            with st.expander("🔧 Fixed SQL (after retry)"):
                st.code(result["fixed_sql"], language="sql")

        if result.get("decomposition"):
            with st.expander("🔬 Query Decomposition"):
                st.json(result["decomposition"])

        db_result = result.get("result") or {}
        rows = db_result.get("rows", [])
        if rows:
            st.markdown(f"**{db_result['row_count']} row(s) returned:**")
            df = pd.DataFrame(rows)
            st.dataframe(
                df, use_container_width=True, height=min(300, 40 + 35 * len(df))
            )
        elif status == "success":
            st.info("Query executed successfully — no rows returned.")

        if result.get("error"):
            st.error(f"⚠️ {result['error']}")

    # Save to history
    st.session_state.messages.append(
        {"role": "assistant", "content": "", "render": render_data}
    )
    st.rerun()
