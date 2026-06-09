from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data import col, MONTH_DE, WEEKDAY_NORM

CHART_COLOR = "#3b82f6"
COLOR_SEQ = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]


def render(df: pd.DataFrame):
    st.markdown("### Daten nach thomasht86/accident-conditions")
    st.markdown("")

    _kpi_row(df)
    st.markdown("")

    c_left, c_right = st.columns([6, 5], gap="medium")
    with c_left:
        _heatmap_tile(df)
    with c_right:
        _monthly_chart(df)

    st.markdown("")
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        _distribution_tile(df)
    with c2:
        _hour_tile(df)
    with c3:
        _distance_tile(df)

    weather_c = col(df, "weather")
    road_c = col(df, "road")
    if weather_c or road_c:
        st.markdown("")
        cols = st.columns(2, gap="medium")
        if weather_c:
            with cols[0]:
                _category_bar(df, weather_c, "Wetterverhältnisse")
        if road_c:
            with cols[1]:
                _category_bar(df, road_c, "Straßenzustand")


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
            st.metric("Unfälle gesamt", f"{len(df):,}")

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

def _heatmap_tile(df: pd.DataFrame):
    lat_c = col(df, "lat")
    lon_c = col(df, "lon")

    with st.container(border=True):
        st.subheader("Dichte der Unglücksorte")
        if lat_c and lon_c:
            df_geo = df[[lat_c, lon_c]].dropna()
            if len(df_geo) == 0:
                st.info("Keine Koordinaten vorhanden.")
                return

            fig = px.density_mapbox(
                df_geo,
                lat=lat_c,
                lon=lon_c,
                zoom=4,
                center={"lat": df_geo[lat_c].median(), "lon": df_geo[lon_c].median()},
                mapbox_style="open-street-map",
                radius=18,
                color_continuous_scale="YlOrRd",
                opacity=0.75,
            )
            fig.update_layout(
                height=380,
                margin=dict(l=0, r=0, t=0, b=0),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Keine Koordinatenspalten (lat/lon) gefunden.")


# ---------------------------------------------------------------------------
# Accidents by time period  (replaces the old monthly chart)
# ---------------------------------------------------------------------------

_ZEITRAUM_OPTS = ["alle Unfälle", "ein Jahr", "ein Monat", "eine Woche"]


def _monthly_chart(df: pd.DataFrame):
    with st.container(border=True):
        h_col, f_col = st.columns([3, 2])
        with h_col:
            st.subheader("Unfälle pro Zeitraum")

        date_c = col(df, "date")
        month_c = col(df, "month")
        year_c = col(df, "year")

        if not date_c or not pd.api.types.is_datetime64_any_dtype(df[date_c]):
            st.info("Keine Datumsspalte gefunden.")
            return

        d_min = df[date_c].min().date()
        d_max = df[date_c].max().date()

        with f_col:
            zeitraum = st.selectbox(
                "Zeitraum auswählen",
                _ZEITRAUM_OPTS,
                key="dash_zeitraum",
            )

        # Date picker only for specific periods
        if zeitraum != "alle Unfälle":
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
        import datetime as _dt
        import calendar as _cal

        if zeitraum == "alle Unfälle":
            if not month_c:
                st.info("Keine Monatsspalte.")
                return
            # Always show all 12 months, zero for months without data
            all_months = pd.DataFrame({"month_num": range(1, 13)})
            actual = df.groupby(df[date_c].dt.month).size().reset_index()
            actual.columns = ["month_num", "Anzahl"]
            counts = all_months.merge(actual, on="month_num", how="left").fillna(0)
            counts["Anzahl"] = counts["Anzahl"].astype(int)
            counts["Label"] = counts["month_num"].map(MONTH_DE)
            subtitle = "Alle Jahre · nach Monat"

        elif zeitraum == "ein Jahr":
            yr = start_date.year
            mask = df[date_c].dt.year == yr
            dff = df[mask]
            # Always show all 12 months
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
            # Always show every day of the month (1 … days_in_month)
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
            # Always show exactly 7 days
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
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title=None,
            yaxis_title="Anzahl Unfälle",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Distribution tile (weekday / month / weather)
# ---------------------------------------------------------------------------

def _distribution_tile(df: pd.DataFrame):
    with st.container(border=True):
        header_col, filter_col = st.columns([2, 2])
        with header_col:
            st.subheader("Verteilung")

        options = {}
        # Prefer the normalised weekday column if present
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
            height=310,
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(orientation="v", font=dict(size=11)),
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Hour of day
# ---------------------------------------------------------------------------

def _hour_tile(df: pd.DataFrame):
    with st.container(border=True):
        st.subheader("Tageszeit der Unfälle")
        hour_c = col(df, "hour")
        if not hour_c:
            st.info("Keine Stundenspalte gefunden.")
            return

        hours = df[hour_c].dropna().astype(int)
        counts = hours.value_counts().sort_index().reset_index()
        counts.columns = ["Stunde", "Anzahl"]

        fig = px.bar(
            counts, x="Stunde", y="Anzahl",
            color_discrete_sequence=["#10b981"],
        )
        fig.update_layout(
            height=310,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(title="Stunde", dtick=2),
            yaxis_title="Anzahl",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Distance distribution
# ---------------------------------------------------------------------------

def _distance_tile(df: pd.DataFrame):
    with st.container(border=True):
        header_col, filter_col = st.columns([2, 2])
        with header_col:
            st.subheader("Entfernung (km)")

        dist_c = col(df, "distance")
        if not dist_c:
            st.info("Keine Entfernungsspalte gefunden.")
            return

        speed_c = col(df, "speed")
        if speed_c:
            with filter_col:
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
            color_discrete_sequence=["#f59e0b"],
            labels={dist_c: "km"},
        )
        fig.update_layout(
            height=310,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="Entfernung (km)", yaxis_title="Anzahl",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Generic category bar
# ---------------------------------------------------------------------------

def _category_bar(df: pd.DataFrame, column: str, title: str):
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
            height=280,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title=None, yaxis_title=None,
            showlegend=False,
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig, use_container_width=True)
