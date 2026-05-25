import streamlit as st
import pandas as pd
import plotly.express as px
from datasets import load_dataset


# -------------------------------------------------
# Seiteneinstellungen
# -------------------------------------------------

st.set_page_config(
    page_title="Unfallanalyse Dashboard",
    page_icon="🚗",
    layout="wide"
)


# -------------------------------------------------
# Titel
# -------------------------------------------------

st.title("🚗 Unfallanalyse Dashboard")
st.markdown(
    "Analyse von Verkehrs- und Unfallbedingungen basierend auf dem Datensatz."
)


# -------------------------------------------------
# Datensatz laden
# -------------------------------------------------

@st.cache_data
def lade_daten():
    dataset = load_dataset("thomasht86/accident-conditions")

    # ersten verfügbaren Split laden
    split_name = list(dataset.keys())[0]

    df = dataset[split_name].to_pandas()

    return df


with st.spinner("Datensatz wird geladen..."):
    df = lade_daten()


# -------------------------------------------------
# Informationen
# -------------------------------------------------

st.success(f"Datensatz erfolgreich geladen: {len(df)} Einträge")


# -------------------------------------------------
# Sidebar Filter
# -------------------------------------------------

st.sidebar.header("🔎 Filter")


# Dynamische Filter für kategorische Spalten
kategorische_spalten = df.select_dtypes(include=["object"]).columns.tolist()

ausgewaehlte_spalte = st.sidebar.selectbox(
    "Spalte auswählen",
    kategorische_spalten
)

if ausgewaehlte_spalte:

    optionen = sorted(df[ausgewaehlte_spalte].dropna().unique())

    ausgewaehlte_werte = st.sidebar.multiselect(
        "Werte auswählen",
        options=optionen,
        default=optionen
    )

    if ausgewaehlte_werte:
        df = df[df[ausgewaehlte_spalte].isin(ausgewaehlte_werte)]


# -------------------------------------------------
# Statistiken
# -------------------------------------------------

st.header("📊 Allgemeine Statistiken")

col1, col2 = st.columns(2)

with col1:
    st.metric("Anzahl Datensätze", len(df))

with col2:
    st.metric("Anzahl Spalten", len(df.columns))


# -------------------------------------------------
# Datentabelle
# -------------------------------------------------

st.header("📋 Datentabelle")

st.dataframe(df, use_container_width=True)


# -------------------------------------------------
# Visualisierungen
# -------------------------------------------------

st.header("📈 Visualisierungen")


# Nur Spalten verwenden die wirklich existieren
categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()


# Histogramm für kategoriale Daten
if len(categorical_cols) > 0:

    spalte_kat = st.selectbox(
        "Kategoriale Spalte für Diagramm auswählen",
        categorical_cols
    )

    fig1 = px.histogram(
        df,
        x=spalte_kat,
        title=f"Verteilung von {spalte_kat}"
    )

    st.plotly_chart(fig1, use_container_width=True)


# Boxplot für numerische Daten
if len(numeric_cols) > 0:

    spalte_num = st.selectbox(
        "Numerische Spalte auswählen",
        numeric_cols
    )

    fig2 = px.box(
        df,
        y=spalte_num,
        title=f"Verteilung von {spalte_num}"
    )

    st.plotly_chart(fig2, use_container_width=True)


# Kreisdiagramm
if len(categorical_cols) > 0:

    pie_spalte = st.selectbox(
        "Spalte für Kreisdiagramm auswählen",
        categorical_cols,
        key="pie"
    )

    pie_data = (
        df[pie_spalte]
        .value_counts()
        .reset_index()
    )

    pie_data.columns = [pie_spalte, "Anzahl"]

    fig3 = px.pie(
        pie_data,
        names=pie_spalte,
        values="Anzahl",
        title=f"Kreisdiagramm für {pie_spalte}"
    )

    st.plotly_chart(fig3, use_container_width=True)


# -------------------------------------------------
# Korrelationsmatrix
# -------------------------------------------------

st.header("📉 Numerische Analyse")

if len(numeric_cols) > 1:

    correlation = df[numeric_cols].corr(numeric_only=True)

    fig4 = px.imshow(
        correlation,
        text_auto=True,
        aspect="auto",
        title="Korrelationsmatrix"
    )

    st.plotly_chart(fig4, use_container_width=True)

else:
    st.info("Nicht genügend numerische Spalten vorhanden.")


# -------------------------------------------------
# Datensatzinformationen
# -------------------------------------------------

with st.expander("🔍 Informationen über den Datensatz"):

    st.write("Anzahl Zeilen:", df.shape[0])
    st.write("Anzahl Spalten:", df.shape[1])

    st.write("Spaltennamen:")
    st.write(df.columns.tolist())

    st.write("Datentypen:")
    st.write(df.dtypes)


# -------------------------------------------------
# Footer
# -------------------------------------------------

st.markdown("---")
st.markdown("Erstellt mit ❤️ und Streamlit")