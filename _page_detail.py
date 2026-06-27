import streamlit as st
from utils.data import col
import pages.detail as _detail

df = st.session_state["df"]

st.markdown("## Verkehrsunfälle in Trondheim")

# ---------------------------------------------------------------------------
# URL ↔ Session-State synchronisieren
# Zwei Fälle:
#   1. Direktaufruf via URL (/details?id=12345): query param → session state
#   2. Navigation aus der Liste: session state → query param (URL aktualisieren)
# ---------------------------------------------------------------------------
qp_id = st.query_params.get("id")
ss_id = st.session_state.get("selected_id")

if qp_id is not None and str(ss_id) != str(qp_id):
    # Direktaufruf oder Browser-Bookmark – session state aus URL befüllen
    id_c = col(df, "id")
    if id_c:
        matches = df[df[id_c].astype(str) == str(qp_id)]
        if len(matches) > 0:
            st.session_state.selected_index = int(matches.index[0])
            st.session_state.selected_id = str(qp_id)
        else:
            st.session_state.selected_index = None
            st.session_state.selected_id = None
elif qp_id is None and ss_id is not None:
    # Aus der Liste navigiert – URL mit korrekter ID befüllen
    st.query_params["id"] = str(ss_id)

# ---------------------------------------------------------------------------
# Skeleton → echter Inhalt
# ---------------------------------------------------------------------------
_slot = st.empty()
with _slot.container():
    _detail.render_skeleton()
with _slot.container():
    _detail.render(df)
