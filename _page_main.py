import streamlit as st
import pages.dashboard as _dashboard

df = st.session_state["df"]

st.markdown("## Verkehrsunfälle in Trondheim")

col_a, col_b = st.columns([1, 1])
with col_a:
    st.page_link("_page_main.py",  label="Dashboard",   icon=":material/dashboard:")
with col_b:
    st.page_link("_page_liste.py", label="Unfallliste", icon=":material/list:")

st.divider()

_slot = st.empty()
with _slot.container():
    _dashboard.render_skeleton()
with _slot.container():
    _dashboard.render(df)
