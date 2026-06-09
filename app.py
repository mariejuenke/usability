import streamlit as st

st.set_page_config(
    page_title="Verkehrsunfälle in Norwegen",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
/* Remove default top padding */
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}

/* Hide sidebar toggle button label */
[data-testid="collapsedControl"] { display: none; }

/* Card hover effect via Streamlit container */
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.10);
    transition: box-shadow 0.2s ease;
}

/* Navigation buttons */
.nav-btn-active > div > button {
    background-color: #1e3a5f !important;
    color: white !important;
    border-color: #1e3a5f !important;
}

/* Metric styling */
[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: #1e3a5f;
}
[data-testid="stMetricLabel"] {
    color: #6b7280 !important;
    font-size: 0.85rem !important;
}

/* Image border-radius */
[data-testid="stImage"] img {
    border-radius: 8px;
}

/* Table / dataframe */
[data-testid="stDataFrame"] {
    border-radius: 8px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "current_page": "dashboard",
    "selected_id": None,
    "selected_index": None,
    "compare_id": None,
    "compare_index": None,
    "split_mode": False,
    "list_page": 0,
    "cmp_page": 0,
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

# ---------------------------------------------------------------------------
# Navigation bar
# ---------------------------------------------------------------------------
nav_c0, nav_c1, nav_c2, nav_c3, nav_c4 = st.columns([5, 1.2, 1.2, 1.2, 0.5])

with nav_c0:
    st.markdown(
        "<h2 style='margin:0; padding:4px 0; color:#1e3a5f;'>🚗 Verkehrsunfälle in Norwegen</h2>",
        unsafe_allow_html=True,
    )

page = st.session_state.current_page

def _nav(label: str, target: str, col_obj, key: str):
    is_active = page == target
    with col_obj:
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, key=key, use_container_width=True, type=btn_type):
            st.session_state.current_page = target
            if target != "detail":
                st.session_state.split_mode = False
            st.rerun()


_nav("Dashboard", "dashboard", nav_c1, "nav_dash")
_nav("Unfallliste", "liste", nav_c2, "nav_liste")

detail_available = st.session_state.selected_index is not None
with nav_c3:
    if detail_available:
        btn_type = "primary" if page == "detail" else "secondary"
        if st.button("Details", key="nav_detail", use_container_width=True, type=btn_type):
            st.session_state.current_page = "detail"
            st.rerun()
    else:
        st.button("Details", key="nav_detail_dis", use_container_width=True, disabled=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Page routing
# ---------------------------------------------------------------------------
import pages.dashboard as _dashboard  # noqa: E402
import pages.liste as _liste          # noqa: E402
import pages.detail as _detail        # noqa: E402

if page == "dashboard":
    _dashboard.render(df)
elif page == "liste":
    _liste.render(df)
elif page == "detail":
    if detail_available:
        _detail.render(df)
    else:
        st.session_state.current_page = "liste"
        st.rerun()
