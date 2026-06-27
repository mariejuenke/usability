import streamlit as st
import streamlit.components.v1 as components
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
    # Aus der Liste navigiert – URL still anpassen ohne neuen History-Eintrag,
    # damit der Browser-Zurück-Button direkt zur Liste zurückführt.
    safe_id = str(ss_id).replace('"', "").replace("'", "").replace("<", "").replace(">", "")
    components.html(
        f'<script>window.parent.history.replaceState(null,"","/details?id={safe_id}");</script>',
        height=0,
    )

# ---------------------------------------------------------------------------
# Skeleton → echter Inhalt
# ---------------------------------------------------------------------------
_slot = st.empty()
with _slot.container():
    _detail.render_skeleton()
with _slot.container():
    _detail.render(df)
