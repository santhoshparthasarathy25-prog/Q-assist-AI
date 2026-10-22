"""Q-assist AI - Streamlit entry point.  Run:  streamlit run app.py"""
import streamlit as st

st.set_page_config(page_title="Q-assist AI", page_icon="🩺", layout="wide")

from src.ui import chat_page, dashboard_page, evaluation_page, knowledge_base_page, settings_page  # noqa: E402
from src.ui.context import build_context  # noqa: E402

CSS = """
<style>
:root { --navy:#0B2545; --teal:#13A89E; --soft:#eef7f6; }
section[data-testid="stSidebar"] { background: var(--navy); }
section[data-testid="stSidebar"] * { color: #ffffff !important; }
section[data-testid="stSidebar"] [data-baseweb="radio"] div { color:#fff !important; }
.qa-hero { background: linear-gradient(90deg, var(--navy), var(--teal)); color:#fff; padding:18px 24px; border-radius:14px; margin-bottom:14px; }
.qa-hero h1 { margin:0; font-size:1.7rem; color:#fff; } .qa-hero p { margin:2px 0 0 0; opacity:.9; }
.qa-badge { display:inline-block; color:#fff; padding:3px 10px; border-radius:12px; font-size:.82rem; margin:2px 6px 2px 0; }
.stButton>button[kind="primary"] { background: var(--teal); border-color: var(--teal); }
@media (max-width: 700px) { .qa-hero h1 { font-size:1.3rem; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource(show_spinner="Starting Q-assist AI (building the search index on first run)...")
def get_context():
    return build_context()


ctx = get_context()
st.markdown("<div class='qa-hero'><h1>🩺 Q-assist AI</h1><p>Intelligent healthcare receptionist demo · LLM · RAG · NLP · Voice "
            "· <b>fictional clinic, simulated workflows, not for clinical use</b></p></div>", unsafe_allow_html=True)

PAGES = {"💬 Chat": chat_page, "📊 Dashboard": dashboard_page, "📚 Knowledge base": knowledge_base_page,
         "✅ Evaluation": evaluation_page, "⚙️ Settings & status": settings_page}
with st.sidebar:
    st.markdown("### Q-assist AI")
    choice = st.radio("Navigate", list(PAGES), label_visibility="collapsed")
    st.markdown("---")
    st.caption("Mode: **LIVE-capable**" if ctx.llm.available else "Mode: **DEMO** (no API key)")
    st.caption("Fictional clinic · synthetic data only · not NHS-approved, not clinically validated.")
    st.caption("Emergency? Call **999**. Urgent advice: **NHS 111**.")

PAGES[choice].render(ctx)
