from __future__ import annotations

import streamlit as st
import pandas as pd
from utils.data import col, get_image

ITEMS_PER_PAGE = 25
_COLS = 5


def render_skeleton():
    st.markdown("### Alle Unfälle")
    st.markdown("")
    cards = "".join(
        f"<div class='sk' style='height:280px;'></div>" for _ in range(ITEMS_PER_PAGE)
    )
    st.markdown(
        f"<div class='sk' style='height:110px; margin-bottom:16px;'></div>"
        f"<div class='sk' style='height:18px; width:180px; margin-bottom:16px;'></div>"
        f"<div style='display:grid; grid-template-columns:repeat({_COLS},1fr); gap:16px;'>"
        f"{cards}</div>",
        unsafe_allow_html=True,
    )


def render(df: pd.DataFrame):  # noqa: PLR0912
    st.markdown("### Alle Unfälle")
    st.markdown("")

    # -----------------------------------------------------------------------
    # Filter bar
    # -----------------------------------------------------------------------
    df_filtered = _apply_filters(df)
    st.markdown(f"**{len(df_filtered):,} Einträge** nach Filterung")
    st.markdown("")

    # -----------------------------------------------------------------------
    # Pagination
    # -----------------------------------------------------------------------
    total = len(df_filtered)
    total_pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    if "list_page" not in st.session_state:
        st.session_state.list_page = 0
    if st.session_state.list_page >= total_pages:
        st.session_state.list_page = 0

    page_idx = st.session_state.list_page
    start = page_idx * ITEMS_PER_PAGE
    end = min(start + ITEMS_PER_PAGE, total)
    page_rows = df_filtered.iloc[start:end]

    # -----------------------------------------------------------------------
    # Card grid (5 columns)
    # -----------------------------------------------------------------------
    for row_start in range(0, len(page_rows), _COLS):
        row_slice = page_rows.iloc[row_start: row_start + _COLS]
        grid_cols = st.columns(_COLS, gap="medium")
        for gc, (df_idx, row) in zip(grid_cols, row_slice.iterrows()):
            with gc:
                _accident_card(row, df_idx, df)

    # -----------------------------------------------------------------------
    # Pagination controls
    # -----------------------------------------------------------------------
    st.markdown("")
    p_left, p_mid, p_right = st.columns([1, 3, 1])
    with p_left:
        if st.button("← Zurück", disabled=page_idx == 0, use_container_width=True):
            st.session_state.list_page -= 1
            st.rerun()
    with p_mid:
        st.markdown(
            f"<p style='text-align:center; color:#6b7280; margin-top:6px;'>"
            f"Seite {page_idx + 1} von {total_pages}</p>",
            unsafe_allow_html=True,
        )
    with p_right:
        if st.button("Weiter →", disabled=page_idx >= total_pages - 1, use_container_width=True):
            st.session_state.list_page += 1
            st.rerun()


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    id_c      = col(df, "id")
    date_c    = col(df, "date")
    weather_c = col(df, "weather")
    light_c   = col(df, "light")
    speed_c   = col(df, "speed")
    units_c   = col(df, "num_units")

    with st.container(border=True):
        f1, f2, f3, f4 = st.columns(4, gap="medium")

        with f1:
            search_id = st.text_input(
                "ID suchen", placeholder="z. B. 255", key="list_search_id"
            )
        with f2:
            weather_vals = []
            if weather_c:
                opts = sorted(df[weather_c].dropna().astype(str).unique())
                weather_vals = st.multiselect(
                    "Wetter", opts, key="list_weather", placeholder="Alle"
                )
        with f3:
            light_vals = []
            if light_c:
                opts = sorted(df[light_c].dropna().astype(str).unique())
                light_vals = st.multiselect(
                    "Lichtverhältnis", opts, key="list_light", placeholder="Alle"
                )
        with f4:
            speed_vals = []
            if speed_c:
                opts = sorted(df[speed_c].dropna().unique().astype(int))
                speed_vals = st.multiselect(
                    "Tempolimit", opts, key="list_speed", placeholder="Alle"
                )

        # Second row: date range + beteiligt slider
        row2_cols = st.columns([2, 2, 3], gap="medium")
        with row2_cols[0]:
            if date_c and pd.api.types.is_datetime64_any_dtype(df[date_c]):
                d_min = df[date_c].min().date()
                d_max = df[date_c].max().date()
                date_from = st.date_input("Von", value=d_min, min_value=d_min,
                                          max_value=d_max, key="list_date_from")
            else:
                date_from = None
        with row2_cols[1]:
            if date_c and pd.api.types.is_datetime64_any_dtype(df[date_c]):
                date_to = st.date_input("Bis", value=d_max, min_value=d_min,
                                        max_value=d_max, key="list_date_to")
            else:
                date_to = None
        with row2_cols[2]:
            units_range = None
            if units_c:
                u_min = int(df[units_c].dropna().min())
                u_max = int(df[units_c].dropna().max())
                if u_min < u_max:
                    units_range = st.slider(
                        "Anzahl beteiligter Fahrzeuge",
                        min_value=u_min, max_value=u_max,
                        value=(u_min, u_max), key="list_units",
                    )

    # Apply filters
    mask = pd.Series([True] * len(df), index=df.index)

    if search_id and id_c:
        mask &= df[id_c].astype(str).str.contains(search_id.strip(), case=False, na=False)
    if weather_vals and weather_c:
        mask &= df[weather_c].astype(str).isin(weather_vals)
    if light_vals and light_c:
        mask &= df[light_c].astype(str).isin(light_vals)
    if speed_vals and speed_c:
        mask &= df[speed_c].isin(speed_vals)
    if date_from and date_to and date_c:
        mask &= df[date_c].dt.date.between(date_from, date_to)
    if units_range and units_c:
        mask &= df[units_c].between(units_range[0], units_range[1])

    return df[mask]


# ---------------------------------------------------------------------------
# Single accident card
# ---------------------------------------------------------------------------

def _accident_card(row: pd.Series, df_idx: int, df: pd.DataFrame = None):
    # Resolve column names from the full df if provided, else from row
    ref = df if df is not None else row.to_frame().T
    id_c = col(ref, "id")
    weather_c = col(ref, "weather")
    light_c = col(ref, "light")
    date_c = col(ref, "date")

    accident_id = row[id_c] if id_c else df_idx
    weather_val = str(row[weather_c]) if weather_c and pd.notna(row.get(weather_c)) else "–"
    light_val = str(row[light_c]) if light_c and pd.notna(row.get(light_c)) else "–"
    date_val = row[date_c] if date_c else None
    if hasattr(date_val, "strftime"):
        date_val = date_val.strftime("%d.%m.%Y")

    with st.container(border=True):
        img_slot = st.empty()
        img_slot.markdown(
            "<div class='sk' style='height:160px;border-radius:8px;'></div>",
            unsafe_allow_html=True,
        )
        img_bytes = get_image(df_idx)
        if img_bytes is not None:
            img_slot.image(img_bytes, use_container_width=True)
        else:
            img_slot.markdown(
                "<div style='height:160px; background:#e5e7eb; border-radius:8px; "
                "display:flex; align-items:center; justify-content:center; color:#9ca3af;'>"
                "Kein Bild</div>",
                unsafe_allow_html=True,
            )

        # Info row
        st.markdown(f"**ID: {accident_id}**")
        info_parts = []
        if date_val and date_val != "NaT":
            info_parts.append(f"<i class='ti ti-calendar' style='font-size:11px;'></i> {date_val}")
        if weather_val != "–":
            info_parts.append(f"<i class='ti ti-cloud' style='font-size:11px;'></i> {weather_val}")
        if light_val != "–":
            info_parts.append(f"<i class='ti ti-bulb' style='font-size:11px;'></i> {light_val}")
        if info_parts:
            st.markdown(
                "<div style='font-size:11.5px; color:#9ca3af; line-height:1.8;'>"
                + "  ·  ".join(info_parts) + "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.caption("Keine Zusatzinfos")

        if st.button("Details ansehen", key=f"card_btn_{df_idx}", use_container_width=True):
            st.session_state.selected_id = accident_id
            st.session_state.selected_index = df_idx
            st.session_state.split_mode = False
            st.session_state.compare_id = None
            st.session_state.compare_index = None
            st.switch_page(st.session_state["_pg_detail"])
