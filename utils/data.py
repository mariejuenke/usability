from __future__ import annotations

import io
import os
import streamlit as st
import pandas as pd
from datasets import load_dataset
from datasets.features import Image as HFImage

try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None


# ---------------------------------------------------------------------------
# Actual column names in thomasht86/accident-conditions
# ---------------------------------------------------------------------------
COLS = {
    "id":         ["nvdb_id"],
    "lat":        ["latitude", "image_lat"],
    "lon":        ["longitude", "image_lon"],
    "date":       ["accident_date"],
    "time":       ["accident_time"],
    "year":       ["year"],
    "month":      ["month"],
    "hour":       ["hour"],
    "weekday":    ["day_of_week"],
    "weather":    ["weather"],
    "light":      ["light_conditions"],
    "road":       ["road_surface_condition"],
    "distance":   ["distance_km"],
    "speed":      ["speed_limit"],
    "region":     ["municipality_name"],
    "severity":   ["accident_type"],
    "road_type":  ["road_type"],
    "temp":       ["temperature"],
    "address":    ["address_text"],
    "road_ref":   ["road_reference"],
    "road_width": ["road_width"],
    "num_cars":   ["num_cars"],
    "num_units":  ["num_units"],
    "num_bikes":  ["num_bicycles"],
    "num_trucks": ["num_trucks"],
}

LABELS_DE = {
    "id": "NVDB-ID", "lat": "Breitengrad", "lon": "Längengrad",
    "date": "Unfalldatum", "time": "Unfallzeit", "year": "Jahr",
    "month": "Monat", "hour": "Stunde", "weekday": "Wochentag",
    "weather": "Wetterverhältnis", "light": "Lichtverhältnis",
    "road": "Straßenzustand", "distance": "Entfernung (km)",
    "speed": "Tempolimit (km/h)", "region": "Gemeinde",
    "severity": "Unfalltyp", "road_type": "Straßentyp",
    "temp": "Temperatur (°C)", "address": "Adresse",
    "road_ref": "Straßenreferenz", "road_width": "Fahrbahnbreite (m)",
    "num_cars": "Anz. PKW", "num_units": "Anz. Fahrzeuge",
    "num_bikes": "Anz. Fahrräder", "num_trucks": "Anz. LKW",
}

# Norwegian day names → German (full)
WEEKDAY_NORM: dict = {
    "mandag": "Montag", "tirsdag": "Dienstag", "onsdag": "Mittwoch",
    "torsdag": "Donnerstag", "fredag": "Freitag", "lørdag": "Samstag", "søndag": "Sonntag",
    "monday": "Montag", "tuesday": "Dienstag", "wednesday": "Mittwoch",
    "thursday": "Donnerstag", "friday": "Freitag", "saturday": "Samstag", "sunday": "Sonntag",
    0: "Montag", 1: "Dienstag", 2: "Mittwoch",
    3: "Donnerstag", 4: "Freitag", 5: "Samstag", 6: "Sonntag",
}

# ---------------------------------------------------------------------------
# Norwegian → German value translations applied at load time
# ---------------------------------------------------------------------------
_TRANSLATIONS: dict = {
    # Wetter (weather)
    "God sikt, opphold":           "Gute Sicht, trocken",
    "God sikt, nedbør":            "Gute Sicht, Niederschlag",
    "Dårlig sikt, nedbør":         "Schlechte Sicht, Niederschlag",
    "Dårlig sikt, tåke eller dis": "Schlechte Sicht, Nebel/Dunst",
    "Dårlig sikt forøvrig":        "Schlechte Sicht (sonstige)",
    # Lichtverhältnis (light_conditions)
    "Dagslys":                     "Tageslicht",
    "Mørkt med vegbelysning":      "Dunkel, beleuchtet",
    "Mørkt uten vegbelysning":     "Dunkel, unbeleuchtet",
    "Tussmørke, skumring":         "Dämmerung (Abend)",
    "Tussmørke, demring":          "Dämmerung (Morgen)",
    # Straßenzustand (road_surface_condition)
    "Tørr, bar veg":               "Trocken, blank",
    "Våt, bar veg":                "Nass, blank",
    "Delvis snø / isbelagt veg":   "Teilweise Schnee-/Eisbelag",
    "Snø / isbelagt veg":          "Schnee-/Eisbelag",
    "Glatt ellers":                "Glatt (sonstige)",
    # Wochentag (day_of_week)
    "Mandag": "Montag", "Tirsdag": "Dienstag", "Onsdag":  "Mittwoch",
    "Torsdag": "Donnerstag", "Fredag": "Freitag",
    "Lørdag": "Samstag", "Søndag": "Sonntag",
    # Straßentyp (road_type)
    "Vanlig veg/gate":      "Normale Straße",
    "Motorveg":             "Autobahn",
    "Motortrafikkveg":      "Kraftfahrstraße",
    "Rampe":                "Auffahrt/Rampe",
    "Gang- / sykkelveg":    "Fuß-/Radweg",
    "Gågate / gatetun":     "Fußgängerzone",
    "Boliggate, boligveg":  "Wohnstraße",
    "Skogsveg":             "Forststraße",
    "Annet (plass m.m.)":   "Sonstiger (Platz o. Ä.)",
    # Unfalltyp (accident_type)
    "Kryssende kjøreretning": "Kreuzende Fahrtrichtung",
    "Motsatt kjøreretning":   "Gegenverkehr",
    "Samme kjøreretning":     "Gleiche Fahrtrichtung",
    "Utforkjøring":           "Abkommen von der Fahrbahn",
    "Fotgjenger/akende":      "Fußgänger/Schlitten",
    "Andre ulykker":          "Sonstige Unfälle",
    # Ortsgebiet (urban_area)
    "Tettsted":      "Ortsgebiet",
    "Ikke tettsted": "Außerorts",
    # Allgemein
    "Ukjent": "Unbekannt",
    "": "",
}

MONTH_DE: dict = {
    1: "Jan", 2: "Feb", 3: "Mär", 4: "Apr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Dez",
}

# Columns too heavy to include in the metadata DataFrame
_SKIP_COLS = {"image", "embedding"}

# Local parquet cache path for the metadata DataFrame (absolute)
_CACHE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".df_cache.parquet"
)


# ---------------------------------------------------------------------------
# Column lookup helpers
# ---------------------------------------------------------------------------

def col(df: pd.DataFrame, semantic: str) -> str | None:
    """Return the actual column name for a semantic field, or None."""
    for c in COLS.get(semantic, [semantic]):
        if c in df.columns:
            return c
    return None


def label(semantic: str) -> str:
    return LABELS_DE.get(semantic, semantic.replace("_", " ").title())


# ---------------------------------------------------------------------------
# Metadata loading  — streaming, no images, local cache
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_df() -> pd.DataFrame:
    """
    Return a metadata-only DataFrame (no images, no embeddings).

    Strategy:
    - If local .parquet cache exists → load instantly.
    - Otherwise download all 6 HuggingFace parquet shards in parallel,
      read only non-image columns (column projection), concatenate, cache.
    """
    cache = os.path.abspath(_CACHE_PATH)
    if os.path.exists(cache):
        return _post_process(pd.read_parquet(cache))

    df = _download_metadata_parallel()

    _safe_save_parquet(df, cache)
    return _post_process(df)


def _safe_save_parquet(df: pd.DataFrame, path: str) -> None:
    """Save DataFrame to parquet, converting any non-serialisable columns to strings."""
    df_save = df.copy()
    for c in df_save.columns:
        col_series = df_save[c].dropna()
        if len(col_series) == 0:
            continue
        sample = col_series.iloc[0]
        if isinstance(sample, (dict, list)):
            df_save[c] = df_save[c].apply(lambda x: str(x) if x is not None else None)
    try:
        df_save.to_parquet(path, index=True)
    except Exception as e:
        # Last resort: drop all object columns that can't be serialised
        import warnings
        warnings.warn(f"Parquet save failed ({e}), retrying without complex columns.")
        safe_cols = []
        for c in df_save.columns:
            try:
                df_save[[c]].to_parquet(io.BytesIO())
                safe_cols.append(c)
            except Exception:
                pass
        df_save[safe_cols].to_parquet(path, index=True)


def _download_metadata_parallel() -> pd.DataFrame:
    import requests
    import io
    import pyarrow.parquet as pq
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Resolve parquet shard URLs via datasets-server API
    api_url = (
        "https://datasets-server.huggingface.co/parquet"
        "?dataset=thomasht86%2Faccident-conditions"
    )
    resp = requests.get(api_url, timeout=30)
    resp.raise_for_status()
    shard_urls = [f["url"] for f in resp.json().get("parquet_files", [])]

    if not shard_urls:
        raise RuntimeError("No parquet shards found via datasets-server API.")

    def _read_shard(url: str) -> pd.DataFrame:
        r = requests.get(url, timeout=300)
        r.raise_for_status()
        buf = io.BytesIO(r.content)
        schema = pq.read_schema(buf)
        meta_cols = [c for c in schema.names if c not in _SKIP_COLS]
        buf.seek(0)
        return pq.read_table(buf, columns=meta_cols).to_pandas()

    frames = [None] * len(shard_urls)
    with ThreadPoolExecutor(max_workers=len(shard_urls)) as pool:
        futures = {pool.submit(_read_shard, url): i for i, url in enumerate(shard_urls)}
        for fut in as_completed(futures):
            idx = futures[fut]
            frames[idx] = fut.result()

    return pd.concat([f for f in frames if f is not None], ignore_index=True)


def _post_process(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure accident_date is datetime
    date_c = col(df, "date")
    if date_c and not pd.api.types.is_datetime64_any_dtype(df[date_c]):
        df[date_c] = pd.to_datetime(df[date_c], errors="coerce")

    # Derive hour from 'accident_time' ('HH:MM')
    time_c = col(df, "time")
    if time_c and col(df, "hour") is None:
        try:
            df["hour"] = (
                pd.to_datetime(df[time_c], format="%H:%M", errors="coerce").dt.hour
            )
        except Exception:
            pass

    # Translate Norwegian string values to German in relevant columns
    _TRANSLATE_COLS = [
        "weather", "light_conditions", "road_surface_condition",
        "day_of_week", "road_type", "accident_type", "urban_area",
    ]
    for c in _TRANSLATE_COLS:
        if c in df.columns and df[c].dtype == object:
            df[c] = df[c].map(lambda v: _TRANSLATIONS.get(v, v) if isinstance(v, str) else v)

    # Derive weekday_de column for charts (full German names)
    wd_c = col(df, "weekday")
    if wd_c and "weekday_de" not in df.columns:
        # After translation, day_of_week already contains German names;
        # just copy it to weekday_de for backwards compatibility
        df["weekday_de"] = df[wd_c]

    # Drop embedding column if it sneaked in
    drop = [c for c in df.columns if "embedding" in c.lower()]
    if drop:
        df = df.drop(columns=drop)

    return df


# ---------------------------------------------------------------------------
# Image loading — per-row parquet slice, cached
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False, ttl=7200)
def get_image(row_index: int) -> bytes | None:
    """
    Return JPEG bytes for the accident image at the given DataFrame row index.
    Uses a single-row parquet slice to avoid loading the full dataset.
    Result is cached in st.cache_data for the session.
    """
    try:
        row_ds = load_dataset(
            "thomasht86/accident-conditions",
            split=f"train[{row_index}:{row_index + 1}]",
        )
        if len(row_ds) == 0:
            return None
        img = row_ds[0].get("image")
        if img is None or not (PILImage and isinstance(img, PILImage.Image)):
            return None
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=80)
        return buf.getvalue()
    except Exception:
        return None


def pil_to_bytes(img) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=80)
    return buf.getvalue()
