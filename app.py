import streamlit as st

st.set_page_config(
    page_title="Verkehrsunfälle in Norwegen",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Sidebar-Nav ausblenden (von st.navigation erzeugt)
st.markdown(
    "<style>[data-testid='stSidebarNav']{display:none!important;}</style>",
    unsafe_allow_html=True,
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
    padding-top: 0.5rem !important;
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

/* ── STICKY NAV
   position:sticky is immune to ancestor transform/will-change restrictions.
   We only need the intermediate elements to not have overflow:hidden. ── */
[data-testid="stVerticalBlock"] > div:has(#site-nav-title) {
    position: -webkit-sticky !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 1000 !important;
    background: #111827 !important;
    padding: 0 2.5rem !important;
    min-height: 52px !important;
    border-bottom: 1px solid rgba(255,255,255,0.09) !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.35) !important;
}

/* Let sticky propagate through intermediate ancestors */
.block-container,
.block-container > div,
[data-testid="stVerticalBlock"] {
    overflow: visible !important;
}

/* ── Nav buttons → text-tab style ── */
[data-testid="stVerticalBlock"] > div:has(#site-nav-title) button {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    padding: 14px 14px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    box-shadow: none !important;
    color: rgba(156, 163, 175, 0.88) !important;
}
[data-testid="stVerticalBlock"] > div:has(#site-nav-title) button:hover {
    color: #e2e8f0 !important;
    background: transparent !important;
    border-bottom-color: rgba(255,255,255,0.18) !important;
}
[data-testid="stVerticalBlock"] > div:has(#site-nav-title) button[kind="primary"] {
    color: #4589C8 !important;
    border-bottom-color: #4589C8 !important;
    font-weight: 600 !important;
}

/* ── Card tiles (also injected into <head> via JS for guaranteed priority) ── */
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

# DataFrame in Session State für Page-Callables verfügbar machen
st.session_state["df"] = df

# ---------------------------------------------------------------------------
# Pages definieren
# ---------------------------------------------------------------------------
import pages.dashboard as _dashboard  # noqa: E402
import pages.liste as _liste          # noqa: E402
import pages.detail as _detail        # noqa: E402


def _page_dashboard():
    _df = st.session_state["df"]
    _content = st.empty()
    with _content.container():
        _dashboard.render_skeleton()
    with _content.container():
        _dashboard.render(_df)


def _page_liste():
    _df = st.session_state["df"]
    _content = st.empty()
    with _content.container():
        _liste.render_skeleton()
    with _content.container():
        _liste.render(_df)


def _page_detail():
    if st.session_state.get("selected_index") is None:
        st.switch_page(pg_liste)
        return
    _df = st.session_state["df"]
    _content = st.empty()
    with _content.container():
        _detail.render_skeleton()
    with _content.container():
        _detail.render(_df)


pg_dashboard = st.Page(_page_dashboard, title="Dashboard", default=True, url_path="dashboard")
pg_liste     = st.Page(_page_liste,     title="Unfallliste",  url_path="liste")
pg_detail    = st.Page(_page_detail,    title="Detail",       url_path="detail")

# Page-Objekte in Session State, damit Unterseiten st.switch_page() nutzen können
st.session_state["_pg_dashboard"] = pg_dashboard
st.session_state["_pg_liste"]     = pg_liste
st.session_state["_pg_detail"]    = pg_detail

# Navigation registrieren (position="hidden" → keine Sidebar-Nav)
pg = st.navigation([pg_dashboard, pg_liste, pg_detail], position="hidden")

# ---------------------------------------------------------------------------
# Navigation bar
# ---------------------------------------------------------------------------
nav_c0, nav_c1, nav_c2, _nav_spacer = st.columns([5, 1.2, 1.2, 0.5])

with nav_c0:
    st.markdown(
        "<h2 style='margin:0; padding:4px 0;'>Verkehrsunfälle in Trondheim</h2>",
        unsafe_allow_html=True,
    )


def _nav(label: str, target_page, col_obj, key: str):
    is_active = pg == target_page
    with col_obj:
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, key=key, use_container_width=True, type=btn_type):
            st.session_state.split_mode = False
            st.switch_page(target_page)


_nav("Dashboard",   pg_dashboard, nav_c1, "nav_dash")
_nav("Unfallliste", pg_liste,     nav_c2, "nav_liste")

# ---------------------------------------------------------------------------
# JS: enforce fixed positioning on the nav bar after each Streamlit re-render
# ---------------------------------------------------------------------------
import streamlit.components.v1 as _components  # noqa: E402
_components.html(
    """
<script>
(function(){
    var pd = window.parent.document;

    // Inject sticky-nav CSS directly into parent <head> (highest priority)
    if (!pd.getElementById('cc-nav-style')) {
        var s = pd.createElement('style');
        s.id = 'cc-nav-style';
        s.textContent =
            '[data-testid="stVerticalBlock"]>div:has(#site-nav-title){' +
            'position:fixed!important;top:0!important;left:0!important;right:0!important;' +
            'z-index:9999!important;background:#111827!important;padding:0 2.5rem!important;' +
            'min-height:52px!important;border-bottom:1px solid rgba(255,255,255,0.09)!important;' +
            'box-shadow:0 2px 12px rgba(0,0,0,0.35)!important;}' +
            '[data-testid="stVerticalBlock"]>div:has(#site-nav-title) button{' +
            'background:transparent!important;border:none!important;' +
            'border-bottom:2px solid transparent!important;border-radius:0!important;' +
            'padding:14px 14px!important;font-size:14px!important;font-weight:500!important;' +
            'color:rgba(156,163,175,0.88)!important;box-shadow:none!important;}' +
            '[data-testid="stVerticalBlock"]>div:has(#site-nav-title) button:hover{' +
            'color:#e2e8f0!important;background:transparent!important;}' +
            '[data-testid="stVerticalBlock"]>div:has(#site-nav-title) button[kind="primary"]{' +
            'color:#4589C8!important;border-bottom-color:#4589C8!important;font-weight:600!important;}';
        pd.head.appendChild(s);
    }

    // Find the OUTERMOST stVerticalBlock's direct child that holds the nav
    function getNavRow() {
        var t = pd.getElementById('site-nav-title');
        if (!t) return null;
        var outer = null;
        var el = t;
        while (el) {
            if (el.getAttribute && el.getAttribute('data-testid') === 'stVerticalBlock') outer = el;
            el = el.parentElement;
        }
        if (!outer) return null;
        for (var i = 0; i < outer.children.length; i++) {
            if (outer.children[i].contains(t)) return outer.children[i];
        }
        return null;
    }

    function fix() {
        var row = getNavRow();
        if (!row) return;
        var cur = row.parentElement;
        while (cur && cur !== pd.body) {
            cur.style.setProperty('transform','none','important');
            cur.style.setProperty('will-change','auto','important');
            cur.style.setProperty('filter','none','important');
            cur.style.setProperty('contain','none','important');
            cur = cur.parentElement;
        }
        row.style.setProperty('position','fixed','important');
        row.style.setProperty('top','0','important');
        row.style.setProperty('left','0','important');
        row.style.setProperty('right','0','important');
        row.style.setProperty('z-index','9999','important');
        row.style.setProperty('background','#111827','important');
        row.style.setProperty('padding','0 2.5rem','important');
        row.style.setProperty('min-height','52px','important');
        row.style.setProperty('border-bottom','1px solid rgba(255,255,255,0.09)','important');
        row.style.setProperty('box-shadow','0 2px 12px rgba(0,0,0,0.35)','important');
    }

    fix();
    new MutationObserver(fix).observe(pd.body, {childList:true, subtree:true});
})();
</script>
""",
    height=0,
)

# ---------------------------------------------------------------------------
# Aktuelle Seite rendern
# ---------------------------------------------------------------------------
pg.run()
