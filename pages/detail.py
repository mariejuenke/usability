from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data import col, get_image, LABELS_DE

COMPARE_PER_PAGE = 6


def render(df: pd.DataFrame):
    idx = st.session_state.get("selected_index")
    if idx is None or idx not in df.index:
        st.error("Kein Unfall ausgewählt.")
        return

    split_mode = st.session_state.get("split_mode", False)
    compare_index = st.session_state.get("compare_index")

    # -----------------------------------------------------------------------
    # Header
    # -----------------------------------------------------------------------
    hdr_left, hdr_right = st.columns([5, 2])
    with hdr_left:
        id_c = col(df, "id")
        accident_id = df.loc[idx, id_c] if id_c else idx
        st.markdown(f"### Unfall #{accident_id}")
    with hdr_right:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("← Zur Liste", use_container_width=True):
                st.session_state.current_page = "liste"
                st.session_state.split_mode = False
                st.rerun()
        with btn_col2:
            if split_mode:
                if st.button("✕ Vergleich beenden", use_container_width=True, type="primary"):
                    st.session_state.split_mode = False
                    st.session_state.compare_id = None
                    st.session_state.compare_index = None
                    st.rerun()
            else:
                if st.button("⚡ Vergleich starten", use_container_width=True):
                    st.session_state.split_mode = True
                    st.session_state.compare_id = None
                    st.session_state.compare_index = None
                    st.rerun()

    st.markdown("")

    # -----------------------------------------------------------------------
    # Layout
    # -----------------------------------------------------------------------
    if not split_mode:
        _render_accident_detail(df, idx)
    else:
        left_col, right_col = st.columns(2, gap="medium")
        with left_col:
            st.markdown("#### Aktueller Unfall")
            _render_accident_detail(df, idx, compact=True)
        with right_col:
            if compare_index is None:
                _render_compare_list(df)
            else:
                cmp_id_c = col(df, "id")
                cmp_id = df.loc[compare_index, cmp_id_c] if cmp_id_c else compare_index
                h1, h2 = st.columns([3, 1])
                with h1:
                    st.markdown(f"#### Vergleich: #{cmp_id}")
                with h2:
                    if st.button("← Andere wählen", key="change_compare"):
                        st.session_state.compare_index = None
                        st.session_state.compare_id = None
                        st.rerun()
                _render_accident_detail(df, compare_index, compact=True)


# ---------------------------------------------------------------------------
# Full accident detail panel
# ---------------------------------------------------------------------------

def _render_accident_detail(df: pd.DataFrame, row_index: int, compact: bool = False):
    row = df.loc[row_index]

    # Image
    img_bytes = get_image(row_index)
    if img_bytes is not None:
        st.image(img_bytes, use_container_width=True)
    else:
        st.markdown(
            "<div style='height:200px; background:#e5e7eb; border-radius:8px; "
            "display:flex; align-items:center; justify-content:center; color:#9ca3af; font-size:14px;'>"
            "Kein Bild verfügbar</div>",
            unsafe_allow_html=True,
        )

    st.markdown("")

    # Key metrics as highlight badges
    _render_key_badges(df, row)

    # All fields + context charts
    if not compact:
        _render_all_fields(df, row)
    else:
        _render_important_fields(df, row)
    _render_mini_charts(df, row, compact=compact)


def _render_key_badges(df: pd.DataFrame, row: pd.Series):
    semantics = ["weather", "light", "road", "speed", "distance"]
    badges = []
    icons = {
        "weather": "🌤",
        "light": "💡",
        "road": "🛣",
        "speed": "⚡",
        "distance": "📏",
    }
    for sem in semantics:
        c = col(df, sem)
        if c and pd.notna(row.get(c)):
            val = row[c]
            if sem == "speed":
                val = f"{int(val)} km/h"
            elif sem == "distance":
                val = f"{float(val):.1f} km"
            badges.append(f"{icons[sem]} <strong>{val}</strong>")

    if badges:
        cols = st.columns(len(badges))
        for bc, badge in zip(cols, badges):
            with bc:
                with st.container(border=True):
                    st.markdown(
                        f"<div style='text-align:center; font-size:13px; padding:4px;'>{badge}</div>",
                        unsafe_allow_html=True,
                    )
    st.markdown("")


def _render_important_fields(df: pd.DataFrame, row: pd.Series):
    """Compact view: only the most relevant fields."""
    priority = ["id", "date", "time", "weather", "light", "road", "speed", "distance", "region"]
    shown = []
    for sem in priority:
        c = col(df, sem)
        if c and pd.notna(row.get(c)):
            shown.append((LABELS_DE.get(sem, sem), row[c]))

    if shown:
        with st.container(border=True):
            for lbl, val in shown:
                if hasattr(val, "strftime"):
                    val = val.strftime("%d.%m.%Y")
                val = str(val).strip('"\'')
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.caption(lbl)
                with c2:
                    st.write(val)


def _render_all_fields(df: pd.DataFrame, row: pd.Series):
    st.markdown("#### Alle Informationen")

    # Group semantically known columns first, then remaining
    priority_semantics = [
        "id", "date", "time", "year", "month", "weekday", "hour",
        "weather", "light", "road", "speed", "distance",
        "region", "severity", "road_type", "lat", "lon",
    ]
    shown_cols = set()
    sections = {}

    for sem in priority_semantics:
        c = col(df, sem)
        if c and c not in shown_cols and pd.notna(row.get(c)):
            sections[sem] = (LABELS_DE.get(sem, sem), row[c])
            shown_cols.add(c)

    # Remaining columns
    other = {}
    for c in df.columns:
        if c not in shown_cols and pd.notna(row.get(c)):
            other[c] = row[c]

    # Render priority fields
    if sections:
        with st.container(border=True):
            st.markdown("**Kerndaten**")
            items = list(sections.values())
            for i in range(0, len(items), 2):
                c1, c2 = st.columns(2)
                for ci, (lbl, val) in zip([c1, c2], items[i: i + 2]):
                    with ci:
                        if hasattr(val, "strftime"):
                            val = val.strftime("%d.%m.%Y")
                        val = str(val).strip('"\'')
                        c_lbl, c_val = st.columns([1, 2])
                        with c_lbl:
                            st.caption(lbl)
                        with c_val:
                            st.write(val)

    # Render other columns
    if other:
        with st.expander("Weitere Felder", expanded=False):
            for c, val in other.items():
                if hasattr(val, "strftime"):
                    val = val.strftime("%d.%m.%Y")
                elif isinstance(val, (dict, list)):
                    val = str(val)
                cl, cv = st.columns([1, 2])
                with cl:
                    st.caption(c)
                with cv:
                    st.markdown(f"**{val}**")


def _render_mini_charts(df: pd.DataFrame, row: pd.Series, compact: bool = False):
    """Context charts — shown in both full and split-screen view."""
    charts = []

    weather_c = col(df, "weather")
    if weather_c and pd.notna(row.get(weather_c)):
        charts.append(("weather", weather_c, "Wetter im Vergleich"))

    dist_c = col(df, "distance")
    if dist_c:
        charts.append(("distance", dist_c, "Entfernung im Vergleich"))

    if not charts:
        return

    st.markdown("#### Einordnung")
    # In compact (split-screen) mode stack vertically to avoid cramping
    if compact:
        containers = [st.container() for _ in charts]
    else:
        containers = st.columns(len(charts), gap="medium")

    for gc, (sem, c_name, title) in zip(containers, charts):
        with gc:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                chart_h = 180 if compact else 200

                if sem == "weather":
                    counts = df[c_name].value_counts().reset_index()
                    counts.columns = ["Kategorie", "Anzahl"]
                    selected_val = str(row[c_name])
                    counts["Farbe"] = counts["Kategorie"].apply(
                        lambda x: "Dieser Unfall" if x == selected_val else "Andere"
                    )
                    fig = px.bar(
                        counts, x="Anzahl", y="Kategorie",
                        orientation="h",
                        color="Farbe",
                        color_discrete_map={"Dieser Unfall": "#ef4444", "Andere": "#93c5fd"},
                    )
                    fig.update_layout(
                        height=chart_h,
                        margin=dict(l=0, r=0, t=0, b=0),
                        showlegend=False,
                        xaxis_title=None, yaxis_title=None,
                        yaxis=dict(autorange="reversed"),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                elif sem == "distance":
                    val = float(row[c_name])
                    fig = px.histogram(
                        df, x=c_name, nbins=25,
                        color_discrete_sequence=["#93c5fd"],
                        labels={c_name: "km"},
                    )
                    fig.add_vline(
                        x=val, line_color="#ef4444", line_width=2,
                        annotation_text=f"{val:.1f} km",
                        annotation_position="top",
                    )
                    fig.update_layout(
                        height=chart_h,
                        margin=dict(l=0, r=0, t=0, b=0),
                        xaxis_title="km", yaxis_title="Anzahl",
                        showlegend=False,
                    )
                    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Compare list (right panel when split_mode is active, no compare selected)
# ---------------------------------------------------------------------------

def _render_compare_list(df: pd.DataFrame):
    st.markdown("#### Zweiten Unfall wählen")

    id_c = col(df, "id")
    weather_c = col(df, "weather")
    light_c = col(df, "light")

    # Mini filter
    search = st.text_input("Suche nach ID", placeholder="z. B. 541", key="cmp_search")
    sel_weather = []
    if weather_c:
        opts = sorted(df[weather_c].dropna().astype(str).unique())
        sel_weather = st.multiselect("Wetter", opts, key="cmp_weather", placeholder="Alle")

    mask = pd.Series([True] * len(df), index=df.index)
    if search and id_c:
        mask &= df[id_c].astype(str).str.contains(search.strip(), case=False, na=False)
    if sel_weather and weather_c:
        mask &= df[weather_c].astype(str).isin(sel_weather)

    filtered = df[mask]

    # Exclude currently selected
    current_idx = st.session_state.get("selected_index")
    if current_idx in filtered.index:
        filtered = filtered.drop(index=current_idx)

    # Paginate
    if "cmp_page" not in st.session_state:
        st.session_state.cmp_page = 0
    total = len(filtered)
    total_pages = max(1, (total + COMPARE_PER_PAGE - 1) // COMPARE_PER_PAGE)
    if st.session_state.cmp_page >= total_pages:
        st.session_state.cmp_page = 0

    start = st.session_state.cmp_page * COMPARE_PER_PAGE
    page_rows = filtered.iloc[start: start + COMPARE_PER_PAGE]

    st.markdown(f"*{total:,} Unfälle*")

    for df_idx, row in page_rows.iterrows():
        _compare_list_item(df, row, df_idx)

    # Pagination
    p1, p2, p3 = st.columns([1, 2, 1])
    with p1:
        if st.button("←", key="cmp_prev", disabled=st.session_state.cmp_page == 0):
            st.session_state.cmp_page -= 1
            st.rerun()
    with p2:
        st.caption(f"Seite {st.session_state.cmp_page + 1}/{total_pages}")
    with p3:
        if st.button("→", key="cmp_next", disabled=st.session_state.cmp_page >= total_pages - 1):
            st.session_state.cmp_page += 1
            st.rerun()


def _compare_list_item(df: pd.DataFrame, row: pd.Series, df_idx: int):
    id_c = col(df, "id")
    weather_c = col(df, "weather")
    light_c = col(df, "light")
    date_c = col(df, "date")

    accident_id = row[id_c] if id_c else df_idx
    date_val = row[date_c] if date_c else None
    if hasattr(date_val, "strftime"):
        date_val = date_val.strftime("%d.%m.%Y")

    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**ID: {accident_id}**")
            parts = []
            if date_val:
                parts.append(str(date_val))
            if weather_c and pd.notna(row.get(weather_c)):
                parts.append(str(row[weather_c]))
            if light_c and pd.notna(row.get(light_c)):
                parts.append(str(row[light_c]))
            st.caption("  ·  ".join(parts) if parts else "–")
        with c2:
            if st.button("Wählen", key=f"cmp_select_{df_idx}", use_container_width=True, type="primary"):
                st.session_state.compare_index = df_idx
                st.session_state.compare_id = accident_id
                st.rerun()
