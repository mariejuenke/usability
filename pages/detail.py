from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data import col, get_image, LABELS_DE, COL_LABELS

COMPARE_PER_PAGE = 6


def render_skeleton():
    meta_cells = "".join(
        f"<div class='sk' style='height:56px;'></div>" for _ in range(5)
    )
    st.markdown(
        # header
        f"<div style='display:grid; grid-template-columns:5fr 2fr; gap:16px; margin-bottom:16px;'>"
        f"  <div class='sk' style='height:40px;'></div>"
        f"  <div class='sk' style='height:40px;'></div>"
        f"</div>"
        # main panel: image + meta
        f"<div style='display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px;'>"
        f"  <div class='sk' style='height:400px;'></div>"
        f"  <div style='display:flex; flex-direction:column; gap:12px;'>{meta_cells}</div>"
        f"</div>"
        # chart area
        f"<div class='sk' style='height:300px;'></div>",
        unsafe_allow_html=True,
    )


def render(df: pd.DataFrame):
    idx = st.session_state.get("selected_index")
    if idx is None or idx not in df.index:
        st.error("Kein Unfall ausgewählt.")
        if st.button("← Zur Liste"):
            st.switch_page("_page_liste.py")
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
                st.session_state.split_mode = False
                st.switch_page("_page_liste.py")
        with btn_col2:
            if split_mode:
                if st.button("Vergleich beenden", use_container_width=True, type="primary"):
                    st.session_state.split_mode = False
                    st.session_state.compare_id = None
                    st.session_state.compare_index = None
                    st.rerun()
            else:
                if st.button("Vergleich starten", use_container_width=True):
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

    # Participants chart — above the detail fields
    _render_participants_chart(df, row)

    # All fields + context charts
    if not compact:
        _render_all_fields(df, row)
    else:
        _render_important_fields(df, row)
    _render_mini_charts(df, row, compact=compact)


def _render_participants_chart(df: pd.DataFrame, row: pd.Series):
    sems = [("num_cars", "PKW"), ("num_trucks", "LKW"), ("num_bikes", "Fahrräder")]
    data = []
    for sem, label in sems:
        c = col(df, sem)
        if c and pd.notna(row.get(c)):
            val = int(row[c])
            data.append({"Typ": label, "Anzahl": val})

    if not data or all(d["Anzahl"] == 0 for d in data):
        return

    with st.container(border=True):
        st.markdown("**Verkehrsteilnehmer**")
        fig = px.bar(
            pd.DataFrame(data), x="Typ", y="Anzahl",
            color_discrete_sequence=["#4589C8"],
            text="Anzahl",
        )
        fig.update_traces(textposition="outside", textfont_size=11, cliponaxis=False)
        fig.update_layout(
            height=260,
            margin=dict(l=0, r=0, t=20, b=10),
            xaxis_title=None,
            yaxis_title="Anzahl",
            yaxis=dict(rangemode="tozero"),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, key=f"chart_participants_{row.name}")
        parts_text = ", ".join(f"{d['Anzahl']} {d['Typ']}" for d in data if d["Anzahl"] > 0)
        st.caption(f"Säulendiagramm – beteiligte Fahrzeuge: {parts_text}.")


def _render_key_badges(df: pd.DataFrame, row: pd.Series):
    semantics = ["weather", "light", "road", "speed", "distance"]
    badges = []
    icons = {
        "weather":  "<i class='ti ti-cloud' style='font-size:14px;'></i>",
        "light":    "<i class='ti ti-bulb' style='font-size:14px;'></i>",
        "road":     "<i class='ti ti-road' style='font-size:14px;'></i>",
        "speed":    "<i class='ti ti-gauge' style='font-size:14px;'></i>",
        "distance": "<i class='ti ti-ruler' style='font-size:14px;'></i>",
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
                        f"<div style='display:flex; justify-content:center; align-items:center;"
                        f"gap:6px; font-size:13px; padding:6px 4px; text-align:center;'>{badge}</div>",
                        unsafe_allow_html=True,
                    )
    st.markdown("")


def _render_important_fields(df: pd.DataFrame, row: pd.Series):
    """Compact view: only the most relevant fields."""
    priority = ["id", "date", "time", "severity", "weather", "light", "road", "speed", "distance", "region"]
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
                    st.caption(COL_LABELS.get(c, c.replace("_", " ").title()))
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
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_weather_{str(row.name)}")
                    total_w = int(counts["Anzahl"].sum())
                    own_row = counts[counts["Kategorie"] == selected_val]
                    own_count = int(own_row["Anzahl"].iloc[0]) if len(own_row) > 0 else 0
                    pct_w = own_count / total_w * 100 if total_w > 0 else 0
                    st.caption(
                        f"Balkendiagramm – häufigste Wetterbedingungen aller Unfälle. "
                        f"Dieser Unfall: »{selected_val}« "
                        f"({own_count} von {total_w}, {pct_w:.0f}%)."
                    )

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
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_distance_{str(row.name)}")
                    valid = df[c_name].dropna()
                    pct_below = (valid <= val).mean() * 100
                    st.caption(
                        f"Histogramm – Entfernung zur nächsten Siedlung ({len(valid)} Unfälle). "
                        f"Dieser Unfall: {val:.1f} km "
                        f"(weiterer Abstand als {pct_below:.0f}% aller Unfälle)."
                    )


# ---------------------------------------------------------------------------
# Similarity scoring & explanation
# ---------------------------------------------------------------------------

def _get_suggestions(df: pd.DataFrame, ref_idx: int, n: int = 6) -> list:
    """Return indices of the n most similar accidents (vectorised, fast)."""
    ref = df.loc[ref_idx]
    cands = df.drop(index=ref_idx)
    scores = pd.Series(0.0, index=cands.index)

    for sem, weight in [("weather", 2), ("light", 2), ("road", 1), ("speed", 1)]:
        c = col(df, sem)
        if c and pd.notna(ref.get(c)):
            scores += (cands[c] == ref[c]).astype(float) * weight

    lat_c, lon_c = col(df, "lat"), col(df, "lon")
    if lat_c and lon_c and pd.notna(ref.get(lat_c)) and pd.notna(ref.get(lon_c)):
        dlat = (cands[lat_c].astype(float) - float(ref[lat_c])) ** 2
        dlon = (cands[lon_c].astype(float) - float(ref[lon_c])) ** 2
        dist = (dlat + dlon) ** 0.5
        scores += (dist < 0.1).astype(float) * 2
        scores += ((dist >= 0.1) & (dist < 0.5)).astype(float) * 1

    return list(scores[scores > 0].nlargest(n).index)


def _explain_match(df: pd.DataFrame, ref_row: pd.Series, cand_row: pd.Series) -> list:
    """Short labels describing why two accidents are similar."""
    parts = []
    for sem, icon, label in [
        ("weather", "<i class='ti ti-cloud'></i>", "Wetter"),
        ("light",   "<i class='ti ti-bulb'></i>",  "Licht"),
        ("road",    "<i class='ti ti-road'></i>",  "Straße"),
        ("speed",   "<i class='ti ti-gauge'></i>", "Tempo"),
    ]:
        c = col(df, sem)
        if c and pd.notna(ref_row.get(c)) and pd.notna(cand_row.get(c)):
            if ref_row[c] == cand_row[c]:
                parts.append(f"{icon} {label}")

    lat_c, lon_c = col(df, "lat"), col(df, "lon")
    if lat_c and lon_c:
        rl, rln = ref_row.get(lat_c), ref_row.get(lon_c)
        cl, cln = cand_row.get(lat_c), cand_row.get(lon_c)
        if all(pd.notna(x) for x in [rl, rln, cl, cln]):
            d = ((float(rl) - float(cl)) ** 2 + (float(rln) - float(cln)) ** 2) ** 0.5
            if d < 0.1:
                parts.append("<i class='ti ti-map-pin'></i> Nah gelegen")
    return parts


# ---------------------------------------------------------------------------
# Compare list (right panel when split_mode is active, no compare selected)
# ---------------------------------------------------------------------------

def _render_compare_list(df: pd.DataFrame):
    st.markdown("#### Zweiten Unfall wählen")
    tab_suggest, tab_all, tab_hist = st.tabs(["Vorschläge", "Alle", "Historie"])

    with tab_suggest:
        _render_suggestions_tab(df)
    with tab_all:
        _render_all_tab(df)
    with tab_hist:
        _render_history_tab(df)


def _render_suggestions_tab(df: pd.DataFrame):
    ref_idx = st.session_state.get("selected_index")
    if ref_idx is None or ref_idx not in df.index:
        st.info("Kein Referenzunfall gewählt.")
        return

    ref_row = df.loc[ref_idx]
    idxs = _get_suggestions(df, ref_idx, n=6)

    if not idxs:
        st.info("Keine ähnlichen Unfälle gefunden.")
        return

    for df_idx in idxs:
        row = df.loc[df_idx]
        tags = _explain_match(df, ref_row, row)
        _compare_list_item(df, row, df_idx, tags=tags)


def _render_all_tab(df: pd.DataFrame):
    id_c        = col(df, "id")
    date_c      = col(df, "date")
    weather_c   = col(df, "weather")
    light_c     = col(df, "light")
    speed_c     = col(df, "speed")
    units_c     = col(df, "num_units")
    severity_c  = col(df, "severity")

    with st.container(border=True):
        f1, f2 = st.columns(2, gap="small")
        with f1:
            search = st.text_input("ID suchen", placeholder="z. B. 541", key="cmp_search")
        with f2:
            sel_weather = []
            if weather_c:
                opts = sorted(df[weather_c].dropna().astype(str).unique())
                sel_weather = st.multiselect("Wetter", opts, key="cmp_weather", placeholder="Alle")

        f3, f4 = st.columns(2, gap="small")
        with f3:
            sel_light = []
            if light_c:
                opts = sorted(df[light_c].dropna().astype(str).unique())
                sel_light = st.multiselect("Lichtverhältnis", opts, key="cmp_light", placeholder="Alle")
        with f4:
            sel_speed = []
            if speed_c:
                opts = sorted(df[speed_c].dropna().unique().astype(int))
                sel_speed = st.multiselect("Tempolimit", opts, key="cmp_speed", placeholder="Alle")

        f5, f6 = st.columns(2, gap="small")
        with f5:
            sel_severity = []
            if severity_c:
                opts = sorted(df[severity_c].dropna().astype(str).unique())
                sel_severity = st.multiselect("Unfalltyp", opts, key="cmp_severity", placeholder="Alle")

        d1, d2, d3 = st.columns([2, 2, 3], gap="small")
        with d1:
            if date_c and pd.api.types.is_datetime64_any_dtype(df[date_c]):
                d_min = df[date_c].min().date()
                d_max = df[date_c].max().date()
                date_from = st.date_input("Von", value=d_min, min_value=d_min, max_value=d_max,
                                          format="DD.MM.YYYY", key="cmp_date_from")
            else:
                date_from = None
        with d2:
            if date_c and pd.api.types.is_datetime64_any_dtype(df[date_c]):
                date_to = st.date_input("Bis", value=d_max, min_value=d_min, max_value=d_max,
                                        format="DD.MM.YYYY", key="cmp_date_to")
            else:
                date_to = None
        with d3:
            units_range = None
            if units_c:
                u_min = int(df[units_c].dropna().min())
                u_max = int(df[units_c].dropna().max())
                if u_min < u_max:
                    units_range = st.slider(
                        "Anzahl beteiligter Fahrzeuge",
                        min_value=u_min, max_value=u_max,
                        value=(u_min, u_max), key="cmp_units",
                    )

    mask = pd.Series([True] * len(df), index=df.index)
    if search and id_c:
        mask &= df[id_c].astype(str).str.contains(search.strip(), case=False, na=False)
    if sel_weather and weather_c:
        mask &= df[weather_c].astype(str).isin(sel_weather)
    if sel_light and light_c:
        mask &= df[light_c].astype(str).isin(sel_light)
    if sel_speed and speed_c:
        mask &= df[speed_c].isin(sel_speed)
    if sel_severity and severity_c:
        mask &= df[severity_c].astype(str).isin(sel_severity)
    if date_from and date_to and date_c:
        mask &= df[date_c].dt.date.between(date_from, date_to)
    if units_range and units_c:
        mask &= df[units_c].between(units_range[0], units_range[1])

    filtered = df[mask]
    current_idx = st.session_state.get("selected_index")
    if current_idx in filtered.index:
        filtered = filtered.drop(index=current_idx)

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

    p1, p2, p3 = st.columns([1, 2, 1])
    with p1:
        if st.button("← Zurück", key="cmp_prev", disabled=st.session_state.cmp_page == 0,
                     use_container_width=True):
            st.session_state.cmp_page -= 1
            st.rerun()
    with p2:
        st.markdown(
            f"<p style='text-align:center; color:#6b7280; margin-top:6px;'>"
            f"Seite {st.session_state.cmp_page + 1} von {total_pages}</p>",
            unsafe_allow_html=True,
        )
    with p3:
        if st.button("Weiter →", key="cmp_next",
                     disabled=st.session_state.cmp_page >= total_pages - 1,
                     use_container_width=True):
            st.session_state.cmp_page += 1
            st.rerun()


def _render_history_tab(df: pd.DataFrame):
    history: list = st.session_state.get("compare_history", [])
    valid = [i for i in history if i in df.index]

    if not valid:
        st.info("Noch kein Vergleich ausgewählt.")
        return

    st.caption(f"{len(valid)} zuletzt verglichen")
    for df_idx in valid:
        row = df.loc[df_idx]
        _compare_list_item(df, row, df_idx, key_suffix="_hist")


def _compare_list_item(
    df: pd.DataFrame,
    row: pd.Series,
    df_idx: int,
    tags: list | None = None,
    key_suffix: str = "",
):
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
            if tags:
                st.markdown(
                    " ".join(
                        f"<span style='background:rgba(59,130,246,0.12);color:#3b82f6;"
                        f"border-radius:4px;padding:1px 6px;font-size:11px;'>{t}</span>"
                        for t in tags
                    ),
                    unsafe_allow_html=True,
                )
        with c2:
            if st.button("Wählen", key=f"cmp_select_{df_idx}{key_suffix}",
                         use_container_width=True, type="primary"):
                # Track in history
                hist = st.session_state.get("compare_history", [])
                hist = [i for i in hist if i != df_idx]
                hist.insert(0, df_idx)
                st.session_state.compare_history = hist[:10]

                st.session_state.compare_index = df_idx
                st.session_state.compare_id = accident_id
                st.rerun()
