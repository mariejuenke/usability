import streamlit as st

st.set_page_config(
    page_title="Verkehrsunfälle in Norwegen",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Tabler Icons (webfont via CDN)
# ---------------------------------------------------------------------------
st.markdown(
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
/* ── Layout ── */
.main .block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
}

/* ── Skeleton shimmer ── */
@keyframes sk-shimmer {
    0%   { background-position: -200% center; }
    100% { background-position:  200% center; }
}
.sk {
    background: linear-gradient(
        90deg,
        rgba(128,128,128,0.10) 25%,
        rgba(128,128,128,0.22) 50%,
        rgba(128,128,128,0.10) 75%
    );
    background-size: 200% 100%;
    animation: sk-shimmer 1.4s ease-in-out infinite;
    border-radius: 4px;
}

/* ── Streamlit chrome ── */
[data-testid="collapsedControl"] { display: none; }
header[data-testid="stHeader"] { display: none !important; }

/* ── Card tiles ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #262730 !important;
    border-radius: 4px !important;
    border-color: rgba(255,255,255,0.07) !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.3) !important;
    transition: box-shadow 0.2s ease !important;
}

/* ── Form elements ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div,
[data-testid="stTextInput"] > div > div input,
.stButton > button {
    border-radius: 4px !important;
}

/* ── Metrics ── */
[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: #9ca3af !important;
    font-size: 0.85rem !important;
}

/* ── Images / tables ── */
[data-testid="stImage"] img { border-radius: 4px !important; }
[data-testid="stDataFrame"] { border-radius: 4px; }

/* ── Tabs linksbündig ── */
[data-baseweb="tab-list"] {
    justify-content: flex-start;
}

/* ── Keyboard focus ── */
.stButton > button:focus-visible {
    outline: 2px solid #4589C8 !important;
    outline-offset: 2px !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:focus-within {
    outline: 2px solid #4589C8 !important;
    box-shadow: 0 0 0 4px rgba(69,137,200,0.25) !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "selected_id": None,
    "selected_index": None,
    "compare_id": None,
    "compare_index": None,
    "split_mode": False,
    "list_page": 0,
    "cmp_page": 0,
    "compare_history": [],
    "show_detail": False,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------------------------------------------------------
# Load data (cached)
# ---------------------------------------------------------------------------
from utils.data import load_df  # noqa: E402 – import after set_page_config
import os as _os

_cache_ready = _os.path.exists(
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".df_cache.parquet")
)

if _cache_ready:
    with st.spinner("Datensatz wird geladen …"):
        df = load_df()
else:
    st.info(
        "**Erster Start** – Metadaten werden von HuggingFace heruntergeladen "
        "(ca. 5–7 Minuten). Beim nächsten Start startet die App sofort."
    )
    with st.spinner(
        "Lade Datensatz-Metadaten (6 Parquet-Shards parallel) …  "
        "Dieser Vorgang findet nur beim ersten Start statt."
    ):
        df = load_df()

st.session_state["df"] = df

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
pg = st.navigation(
    [
        st.Page("_page_main.py",   title="Dashboard",    default=True),
        st.Page("_page_liste.py",  title="Unfallliste",  url_path="list"),
        st.Page("_page_detail.py", title="Unfalldetail", url_path="details"),
    ],
    position="hidden",
)
pg.run()
