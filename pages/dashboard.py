from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data import col, MONTH_DE, WEEKDAY_NORM

CHART_COLOR = "#4589C8"  # Trondheim coat-of-arms blue
COLOR_SEQ = ["#4589C8", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]

# Chart heights per row — keep equal within each row so tiles align
_H_ROW1_MAP  = 380   # heatmap (no controls above, so taller chart)
_H_ROW1_BAR  = 244   # time chart (controls above eat ~136 px → total matches heatmap)
_H_ROW2      = 300   # weather / road
_H_ROW3      = 300   # distribution / hour / distance


_SK = "<div class='sk' style='height:{h}px; margin-bottom:0;'></div>"
_SK_ROW = "<div style='display:grid; grid-template-columns:{cols}; gap:16px; margin-bottom:16px;'>{cells}</div>"


def render_skeleton():
    st.markdown("### Daten nach thomasht86/accident-conditions")
    st.markdown("")
    html = (
        # KPI row
        _SK_ROW.format(cols="1fr 1fr 1fr 1fr",      cells=_SK.format(h=80)  * 4) +
        # Row 1: map + time
        _SK_ROW.format(cols="6fr 5fr",               cells=_SK.format(h=460) * 2) +
        # Row 2: weather + road
        _SK_ROW.format(cols="1fr 1fr",               cells=_SK.format(h=370) * 2) +
        # Row 3: distribution / hour / distance
        _SK_ROW.format(cols="1fr 1fr 1fr",           cells=_SK.format(h=370) * 3)
    )
    st.markdown(html, unsafe_allow_html=True)


def render(df: pd.DataFrame):
    st.markdown("### Daten nach thomasht86/accident-conditions")
    st.markdown("")

    _kpi_row(df)
    st.divider()

    # --- Row 1: Geo + Zeit ---
    _section_header(
        "Geografische Lage & Zeitreihe",
        "Hotspot-Karte der Unfallschwerpunkte und zeitliche Häufigkeit im gewählten Zeitraum.",
    )
    c_left, c_right = st.columns([6, 5], gap="medium")
    with c_left:
        _heatmap_tile(df, chart_height=_H_ROW1_MAP)
    with c_right:
        _monthly_chart(df, chart_height=_H_ROW1_BAR)

    # --- Row 2: Wetter + Straße + Tempolimit ---
    weather_c = col(df, "weather")
    road_c    = col(df, "road")
    speed_c   = col(df, "speed")
    row2_tiles = [
        (weather_c, lambda c: _category_bar(df, c, "Wetterverhältnisse", chart_height=_H_ROW2)),
        (road_c,    lambda c: _category_bar(df, c, "Straßenzustand",     chart_height=_H_ROW2)),
        (speed_c,   lambda _: _speed_tile(df, chart_height=_H_ROW2)),
    ]
    visible = [(c, fn) for c, fn in row2_tiles if c]
    if visible:
        _section_header(
            "Umgebungsbedingungen",
            "Einfluss von Wetter, Straßenzustand und Geschwindigkeitsbegrenzung auf das Unfallgeschehen.",
        )
        r2_cols = st.columns(len(visible), gap="medium")
        for gc, (c, fn) in zip(r2_cols, visible):
            with gc:
                fn(c)

    # --- Row 3: Verteilung / Tageszeit / Entfernung ---
    _section_header(
        "Muster & Statistik",
        "Verteilung nach Wochentag oder Monat, tageszeitliche Häufung und Entfernung zur nächsten Siedlung.",
    )
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        _distribution_tile(df, chart_height=_H_ROW3)
    with c2:
        _hour_tile(df, chart_height=_H_ROW3)
    with c3:
        _distance_tile(df, chart_height=_H_ROW3)


# ---------------------------------------------------------------------------
# Section header helper
# ---------------------------------------------------------------------------

def _section_header(title: str, description: str):
    st.markdown(
        f"<div style='margin: 32px 0 12px 0; padding-left: 12px;"
        f"border-left: 3px solid #4589C8;'>"
        f"<div style='font-size:0.78rem; font-weight:600; text-transform:uppercase;"
        f"letter-spacing:0.06em; color:#9ca3af; margin-bottom:3px;'>{title}</div>"
        f"<div style='font-size:0.83rem; color:#6b7280;'>{description}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------

def _kpi_row(df: pd.DataFrame):
    cols = st.columns(4, gap="medium")
    date_c = col(df, "date")
    dist_c = col(df, "distance")
    weather_c = col(df, "weather")

    with cols[0]:
        with st.container(border=True):
            badge_html = ""
            if date_c and pd.api.types.is_datetime64_any_dtype(df[date_c]):
                year_counts = df.groupby(df[date_c].dt.year).size()
                if len(year_counts) >= 2:
                    years = sorted(year_counts.index)
                    last, prev = years[-1], years[-2]
                    if year_counts[prev] > 0:
                        pct = (year_counts[last] - year_counts[prev]) / year_counts[prev] * 100
                        color = "#ef4444" if pct > 0 else "#22c55e"
                        badge_html = (
                            f"<span style='background:{color};color:#fff;border-radius:999px;"
                            f"padding:2px 8px;font-size:12px;font-weight:600;margin-left:8px;"
                            f"vertical-align:middle;'>{pct:+.1f}%&nbsp;({prev}→{last})</span>"
                        )
            st.markdown(
                f"<div style='font-size:0.85rem;color:#9ca3af;margin-bottom:2px;'>Unfälle gesamt</div>"
                f"<div style='font-size:1.8rem;font-weight:700;line-height:1.2;'>"
                f"{len(df):,}{badge_html}</div>",
                unsafe_allow_html=True,
            )

    with cols[1]:
        if date_c and pd.api.types.is_datetime64_any_dtype(df[date_c]):
            d_min = df[date_c].min()
            d_max = df[date_c].max()
            with st.container(border=True):
                st.metric("Zeitraum", f"{d_min.year} – {d_max.year}")
        else:
            with st.container(border=True):
                st.metric("Spalten", len(df.columns))

    with cols[2]:
        if dist_c:
            avg = df[dist_c].mean()
            with st.container(border=True):
                st.metric("Ø Entfernung", f"{avg:.1f} km")
        else:
            with st.container(border=True):
                st.metric("Einträge", f"{len(df):,}")

    with cols[3]:
        if weather_c:
            top = df[weather_c].mode()
            val = str(top.iloc[0]) if len(top) > 0 else "–"
            with st.container(border=True):
                st.metric("Häuf. Wetter", val[:20])
        else:
            speed_c = col(df, "speed")
            if speed_c:
                with st.container(border=True):
                    st.metric("Ø Tempolimit", f"{df[speed_c].mean():.0f} km/h")
            else:
                with st.container(border=True):
                    st.metric("Kategorien", len(df.select_dtypes("object").columns))


# ---------------------------------------------------------------------------
# Heatmap
# ---------------------------------------------------------------------------

def _heatmap_tile(df: pd.DataFrame, chart_height: int = 380):
    lat_c = col(df, "lat")
    lon_c = col(df, "lon")

    with st.container(border=True):
        st.subheader("Dichte der Unglücksorte")
        chart_slot = st.empty()
        chart_slot.markdown(
            f"<div class='sk' style='height:{chart_height}px;border-radius:6px;'></div>",
            unsafe_allow_html=True,
        )
        if lat_c and lon_c:
            df_geo = df[[lat_c, lon_c]].dropna()
            if len(df_geo) == 0:
                chart_slot.info("Keine Koordinaten vorhanden.")
                return

            fig = px.density_mapbox(
                df_geo,
                lat=lat_c,
                lon=lon_c,
                zoom=7,
                center={"lat": 63.43, "lon": 10.39},
                mapbox_style="open-street-map",
                radius=18,
                color_continuous_scale="YlOrRd",
                opacity=0.75,
            )
            fig.update_layout(
                height=chart_height,
                margin=dict(l=0, r=0, t=0, b=0),
                coloraxis_showscale=False,
            )
            chart_slot.plotly_chart(fig, use_container_width=True)
        else:
            chart_slot.info("Keine Koordinatenspalten (lat/lon) gefunden.")


# ---------------------------------------------------------------------------
# Accidents by time period
# ---------------------------------------------------------------------------

_ZEITRAUM_OPTS = ["ein Jahr", "ein Monat", "eine Woche"]


def _monthly_chart(df: pd.DataFrame, chart_height: int = 295):
    with st.container(border=True):
        h_col, f_col = st.columns([3, 2])
        with h_col:
            st.subheader("Unfälle pro Zeitraum")

        date_c = col(df, "date")

        if not date_c or not pd.api.types.is_datetime64_any_dtype(df[date_c]):
            st.info("Keine Datumsspalte gefunden.")
            return

        d_min = df[date_c].min().date()
        d_max = df[date_c].max().date()
        available_years = sorted(df[date_c].dt.year.dropna().unique().astype(int), reverse=True)

        with f_col:
            zeitraum = st.selectbox(
                "Zeitraum auswählen",
                _ZEITRAUM_OPTS,
                key="dash_zeitraum",
            )

        import datetime as _dt
        import calendar as _cal

        if zeitraum == "ein Jahr":
            default_idx = available_years.index(2024) if 2024 in available_years else 0
            sel_year = st.selectbox("Jahr", available_years, index=default_idx, key="dash_year")
            start_date = _dt.date(sel_year, 1, 1)

        elif zeitraum == "ein Monat":
            y_col, m_col = st.columns(2)
            with y_col:
                sel_year = st.selectbox("Jahr", available_years, key="dash_month_year")
            avail_months = sorted(
                df[df[date_c].dt.year == sel_year][date_c].dt.month.dropna().unique().astype(int)
            )
            with m_col:
                sel_month = st.selectbox(
                    "Monat", avail_months,
                    format_func=lambda m: MONTH_DE.get(m, str(m)),
                    key="dash_month_month",
                )
            start_date = _dt.date(sel_year, sel_month, 1)

        elif zeitraum == "eine Woche":
            start_date = st.date_input(
                "Anfangsdatum",
                value=d_max,
                min_value=d_min,
                max_value=d_max,
                format="DD/MM/YYYY",
                key="dash_start_date",
            )

        else:
            start_date = None

        # ---- aggregate ----
        if zeitraum == "ein Jahr":
            yr = start_date.year
            mask = df[date_c].dt.year == yr
            dff = df[mask]
            all_months = pd.DataFrame({"month_num": range(1, 13)})
            if len(dff) > 0:
                actual = dff.groupby(dff[date_c].dt.month).size().reset_index()
                actual.columns = ["month_num", "Anzahl"]
            else:
                actual = pd.DataFrame({"month_num": pd.Series(dtype=int), "Anzahl": pd.Series(dtype=int)})
            counts = all_months.merge(actual, on="month_num", how="left").fillna(0)
            counts["Anzahl"] = counts["Anzahl"].astype(int)
            counts["Label"] = counts["month_num"].map(MONTH_DE)
            subtitle = f"Jahr {yr} · nach Monat"

        elif zeitraum == "ein Monat":
            yr, mo = start_date.year, start_date.month
            days_in_month = _cal.monthrange(yr, mo)[1]
            mask = (df[date_c].dt.year == yr) & (df[date_c].dt.month == mo)
            dff = df[mask]
            all_days = pd.DataFrame({"day_num": range(1, days_in_month + 1)})
            if len(dff) > 0:
                actual = dff.groupby(dff[date_c].dt.day).size().reset_index()
                actual.columns = ["day_num", "Anzahl"]
            else:
                actual = pd.DataFrame({"day_num": pd.Series(dtype=int), "Anzahl": pd.Series(dtype=int)})
            counts = all_days.merge(actual, on="day_num", how="left").fillna(0)
            counts["Anzahl"] = counts["Anzahl"].astype(int)
            counts["Label"] = counts["day_num"].astype(str) + "."
            subtitle = f"{MONTH_DE.get(mo, mo)} {yr} · nach Tag"

        else:  # eine Woche
            week_days = [start_date + _dt.timedelta(days=i) for i in range(7)]
            all_days = pd.DataFrame({"date_val": week_days})
            end_date = start_date + _dt.timedelta(days=7)
            mask = (df[date_c].dt.date >= start_date) & (df[date_c].dt.date < end_date)
            dff = df[mask]
            if len(dff) > 0:
                actual = dff.groupby(dff[date_c].dt.date).size().reset_index()
                actual.columns = ["date_val", "Anzahl"]
            else:
                actual = pd.DataFrame({"date_val": pd.Series(dtype=object), "Anzahl": pd.Series(dtype=int)})
            counts = all_days.merge(actual, on="date_val", how="left").fillna(0)
            counts["Anzahl"] = counts["Anzahl"].astype(int)
            counts["Label"] = counts["date_val"].apply(lambda d: d.strftime("%a %d.%m"))
            subtitle = f"Woche ab {start_date.strftime('%d.%m.%Y')}"

        # ---- chart ----
        st.caption(subtitle)
        fig = px.bar(
            counts, x="Label", y="Anzahl",
            color_discrete_sequence=[CHART_COLOR],
            text="Anzahl",
        )
        fig.update_traces(textposition="outside", textfont_size=10)
        fig.update_layout(
            height=chart_height,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title=None,
            yaxis_title="Anzahl Unfälle",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Generic category bar
# ---------------------------------------------------------------------------

def _category_bar(df: pd.DataFrame, column: str, title: str, chart_height: int = 300):
    with st.container(border=True):
        st.subheader(title)
        counts = df[column].value_counts().head(10).reset_index()
        counts.columns = ["Kategorie", "Anzahl"]
        fig = px.bar(
            counts, x="Anzahl", y="Kategorie",
            orientation="h",
            color_discrete_sequence=[CHART_COLOR],
            text="Anzahl",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            height=chart_height,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title=None, yaxis_title=None,
            showlegend=False,
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Speed limit tile
# ---------------------------------------------------------------------------

def _speed_tile(df: pd.DataFrame, chart_height: int = 300):
    speed_c = col(df, "speed")
    if not speed_c:
        return
    with st.container(border=True):
        st.subheader("Unfälle nach Tempolimit")
        counts = (
            df[speed_c].dropna().astype(int)
            .value_counts().reset_index()
        )
        counts.columns = ["km/h", "Anzahl"]
        counts = counts.sort_values("km/h")
        fig = px.bar(
            counts, x="km/h", y="Anzahl",
            color_discrete_sequence=[CHART_COLOR],
            text="Anzahl",
        )
        fig.update_traces(textposition="outside", textfont_size=10)
        fig.update_layout(
            height=chart_height,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(title="Tempolimit (km/h)", type="category"),
            yaxis_title="Anzahl Unfälle",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Distribution tile (weekday / month / weather)
# ---------------------------------------------------------------------------

def _distribution_tile(df: pd.DataFrame, chart_height: int = 300):
    with st.container(border=True):
        header_col, filter_col = st.columns([2, 2])
        with header_col:
            st.subheader("Verteilung")

        options = {}
        if "weekday_de" in df.columns:
            options["nach Wochentag"] = "weekday_de"
        elif col(df, "weekday"):
            options["nach Wochentag"] = col(df, "weekday")
        month_c = col(df, "month")
        if month_c:
            options["nach Monat"] = month_c
        light_c = col(df, "light")
        if light_c:
            options["nach Lichtverhältnis"] = light_c

        if not options:
            st.info("Keine geeignete Spalte gefunden.")
            return

        with filter_col:
            choice = st.selectbox("Anzeigen", list(options.keys()), key="dash_dist")

        chosen_c = options[choice]
        ser = df[chosen_c].dropna()

        if choice == "nach Monat":
            ser = ser.map(MONTH_DE)
        elif choice == "nach Wochentag" and ser.dtype != object:
            ser = ser.map(WEEKDAY_NORM)

        counts = ser.value_counts().reset_index()
        counts.columns = ["Kategorie", "Anzahl"]

        fig = px.pie(
            counts, names="Kategorie", values="Anzahl",
            color_discrete_sequence=COLOR_SEQ,
            hole=0.35,
        )
        fig.update_layout(
            height=chart_height,
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(orientation="v", font=dict(size=11)),
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Hour of day
# ---------------------------------------------------------------------------

def _hour_tile(df: pd.DataFrame, chart_height: int = 300):
    with st.container(border=True):
        header_col, filter_col = st.columns([2, 2])
        with header_col:
            st.subheader("Zeitliche Verteilung")

        hour_c = col(df, "hour")
        date_c = col(df, "date")

        options = []
        if hour_c:
            options.append("Tageszeit")
        if date_c and pd.api.types.is_datetime64_any_dtype(df[date_c]):
            options.append("Monatlich (alle Jahre)")

        if not options:
            st.info("Keine Zeitdaten gefunden.")
            return

        with filter_col:
            view = st.selectbox("Ansicht", options, key="dash_time_view") if len(options) > 1 else options[0]

        if view == "Tageszeit":
            hours = df[hour_c].dropna().astype(int)
            counts = hours.value_counts().sort_index().reset_index()
            counts.columns = ["Stunde", "Anzahl"]
            fig = px.bar(counts, x="Stunde", y="Anzahl", color_discrete_sequence=[CHART_COLOR])
            fig.update_layout(
                height=chart_height,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(title="Stunde", dtick=2),
                yaxis_title="Anzahl",
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            all_months = pd.DataFrame({"month_num": range(1, 13)})
            actual = df.groupby(df[date_c].dt.month).size().reset_index()
            actual.columns = ["month_num", "Anzahl"]
            counts = all_months.merge(actual, on="month_num", how="left").fillna(0)
            counts["Anzahl"] = counts["Anzahl"].astype(int)
            counts["Label"] = counts["month_num"].map(MONTH_DE)
            fig = px.bar(
                counts, x="Label", y="Anzahl",
                color_discrete_sequence=[CHART_COLOR],
                text="Anzahl",
            )
            fig.update_traces(textposition="outside", textfont_size=10)
            fig.update_layout(
                height=chart_height,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title=None,
                yaxis_title="Anzahl Unfälle",
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Distance distribution
# ---------------------------------------------------------------------------

def _distance_tile(df: pd.DataFrame, chart_height: int = 300):
    with st.container(border=True):
        st.subheader("Entfernung (km)")

        dist_c = col(df, "distance")
        if not dist_c:
            st.info("Keine Entfernungsspalte gefunden.")
            return

        speed_c = col(df, "speed")
        if speed_c:
            speeds = sorted(df[speed_c].dropna().unique().astype(int))
            sel_speed = st.multiselect(
                "Tempolimit", speeds,
                default=speeds, key="dash_speed",
                placeholder="Alle",
            )
            dff = df if not sel_speed else df[df[speed_c].isin(sel_speed)]
        else:
            dff = df

        fig = px.histogram(
            dff, x=dist_c, nbins=30,
            color_discrete_sequence=[CHART_COLOR],
            labels={dist_c: "km"},
        )
        fig.update_layout(
            height=chart_height,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="Entfernung (km)", yaxis_title="Anzahl",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
