import io
import os
from datetime import date as dt_date

import folium
import pandas as pd
import streamlit as st
from folium.plugins import MarkerCluster

st.set_page_config(page_title="Air Quality Europe — EAQI", page_icon="🌍", layout="wide")

# -----------------------------
# CONFIG
# -----------------------------
DEFAULT_XLSX = "air_quality_history.xlsx"  # fichier local dans le dossier
GOOD_MAX = 40
MEDIUM_MAX = 80

# COULEURS (alignées légende)
COLOR_GOOD = "#0078FF"   # bleu
COLOR_MED = "#FFA500"    # orange
COLOR_BAD = "#DC143C"    # rouge
COLOR_UNKNOWN = "#A0A0A0"

# Bordure des points (pour éviter impression de “vert” / mélange de teintes)
STROKE_COLOR = "#111111"

ISO2_TO_COUNTRY_FR = {
    "AL": "Albanie",
    "AT": "Autriche",
    "BA": "Bosnie-Herzégovine",
    "BE": "Belgique",
    "BG": "Bulgarie",
    "CH": "Suisse",
    "CZ": "Tchéquie",
    "DE": "Allemagne",
    "DK": "Danemark",
    "EE": "Estonie",
    "ES": "Espagne",
    "FI": "Finlande",
    "FR": "France",
    "GB": "Royaume-Uni",
    "GR": "Grèce",
    "HR": "Croatie",
    "HU": "Hongrie",
    "IE": "Irlande",
    "IS": "Islande",
    "IT": "Italie",
    "LT": "Lituanie",
    "LU": "Luxembourg",
    "LV": "Lettonie",
    "MD": "Moldavie",
    "ME": "Monténégro",
    "MK": "Macédoine du Nord",
    "MT": "Malte",
    "NL": "Pays-Bas",
    "NO": "Norvège",
    "PL": "Pologne",
    "PT": "Portugal",
    "RO": "Roumanie",
    "RS": "Serbie",
    "SE": "Suède",
    "SI": "Slovénie",
    "SK": "Slovaquie",
    "UA": "Ukraine",
}


def country_name(code: str) -> str:
    if not isinstance(code, str):
        return "Inconnu"
    c = code.strip().upper()
    return ISO2_TO_COUNTRY_FR.get(c, c)


def eaqi_label(v: float) -> str:
    if pd.isna(v):
        return "Inconnu"
    if v <= GOOD_MAX:
        return "Bon"
    if v <= MEDIUM_MAX:
        return "Moyen"
    return "Mauvais"


def eaqi_color(v: float) -> str:
    """Couleurs strictement alignées avec la légende."""
    if pd.isna(v):
        return COLOR_UNKNOWN
    if v <= GOOD_MAX:
        return COLOR_GOOD
    if v <= MEDIUM_MAX:
        return COLOR_MED
    return COLOR_BAD


def legend_html() -> str:
    return f"""
    <div style="
        position: fixed; bottom: 30px; left: 30px; z-index: 9999;
        background: white; padding: 10px 12px; border-radius: 10px;
        box-shadow: 0 6px 22px rgba(0,0,0,0.15); font-size: 13px;
    ">
      <div style="font-weight:700; margin-bottom:6px;">EAQI — Légende</div>
      <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
        <span style="width:12px;height:12px;border-radius:50%;background:{COLOR_GOOD};display:inline-block;"></span>
        <span><b>Bon</b> (≤ {GOOD_MAX})</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
        <span style="width:12px;height:12px;border-radius:50%;background:{COLOR_MED};display:inline-block;"></span>
        <span><b>Moyen</b> ({GOOD_MAX}–{MEDIUM_MAX})</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
        <span style="width:12px;height:12px;border-radius:50%;background:{COLOR_BAD};display:inline-block;"></span>
        <span><b>Mauvais</b> (&gt; {MEDIUM_MAX})</span>
      </div>
    </div>
    """


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


def fix_single_column_csv_like(df: pd.DataFrame) -> pd.DataFrame:
    """
    Si ton xlsx contient tout dans une seule colonne dont le "header" ressemble à:
    city,country,date,...,longitude
    alors on reconstruit un vrai dataframe avec ces colonnes.
    """
    if df.shape[1] != 1:
        return df

    header = str(df.columns[0])
    if "," not in header:
        return df

    lines = [header] + df.iloc[:, 0].astype(str).tolist()
    csv_text = "\n".join(lines)
    return pd.read_csv(io.StringIO(csv_text))


@st.cache_data(show_spinner=False)
def load_excel_local(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, engine="openpyxl", sheet_name=0)
    df = fix_single_column_csv_like(df)
    df = normalize_columns(df)
    return df


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    needed = {"city", "country", "date", "latitude", "longitude", "european_aqi"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(
            f"Colonnes manquantes: {sorted(missing)} | Colonnes trouvées: {list(df.columns)}"
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["european_aqi"] = pd.to_numeric(df["european_aqi"], errors="coerce")

    df["country_name"] = df["country"].apply(country_name)

    df = df.dropna(subset=["date", "latitude", "longitude", "european_aqi", "city", "country"])
    return df


def city_means_for_day(df_day: pd.DataFrame) -> pd.DataFrame:
    out = (
        df_day.groupby(["city", "country", "country_name", "latitude", "longitude"], as_index=False)
        .agg(european_aqi=("european_aqi", "mean"))
    )
    out["label"] = out["european_aqi"].apply(eaqi_label)
    out["color"] = out["european_aqi"].apply(eaqi_color)
    return out


# -----------------------------
# APP
# -----------------------------
st.title("🌍 Air Quality Europe")

xlsx_path = DEFAULT_XLSX
if not os.path.exists(xlsx_path):
    st.error(f"Fichier introuvable: {xlsx_path} (mets le .xlsx dans le même dossier que main.py)")
    st.stop()

df_raw = load_excel_local(xlsx_path)

with st.sidebar:
    st.header("Debug")
    st.write("Colonnes détectées :", list(df_raw.columns))
    st.write("Lignes :", len(df_raw))

df = prepare(df_raw)

# Filtres
dates = sorted(df["date"].unique())
with st.sidebar:
    st.header("Filtres")
    selected_date = st.selectbox("Jour", dates, index=len(dates) - 1)

df_day = df[df["date"] == selected_date].copy()

countries = sorted(df_day["country_name"].unique())
with st.sidebar:
    selected_countries = st.multiselect("Pays (optionnel)", countries, default=[])

if selected_countries:
    df_day = df_day[df_day["country_name"].isin(selected_countries)]

points = city_means_for_day(df_day)

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("📅 Date", str(selected_date))
c2.metric("🏙️ Villes", int(points["city"].nunique()))
c3.metric("🏳️ Pays", int(points["country"].nunique()))
c4.metric("🌫️ EAQI moyen", float(points["european_aqi"].mean()) if len(points) else 0.0)

# Options affichage
with st.sidebar:
    st.header("Affichage")
    use_clusters = st.checkbox("Regrouper les points", value=True)
    radius = st.slider("Taille des points", 3, 15, 7)

# Carte
if len(points):
    center_lat = float(points["latitude"].mean())
    center_lon = float(points["longitude"].mean())
else:
    center_lat, center_lon = 50.0, 10.0

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=4,
    tiles="OpenStreetMap",
    control_scale=True
)
m.get_root().html.add_child(folium.Element(legend_html()))

layer = MarkerCluster(disableClusteringAtZoom=7) if use_clusters else folium.FeatureGroup(name="Villes")

for _, r in points.iterrows():
    popup_html = f"""
    <div style="font-size:13px">
      <div><b>{r['city']}</b> — {r['country_name']}</div>
      <div>EAQI moyen: <b>{r['european_aqi']:.1f}</b> ({r['label']})</div>
      <div style="opacity:0.8">Lat: {r['latitude']:.4f} | Lon: {r['longitude']:.4f}</div>
    </div>
    """

    # Bordure forcée en noir + fill color strictement selon légende
    folium.CircleMarker(
        location=[r["latitude"], r["longitude"]],
        radius=radius,
        color=STROKE_COLOR,          # bordure noire
        weight=1,
        fill=True,
        fill_color=r["color"],       # bleu/orange/rouge uniquement
        fill_opacity=0.9,
        popup=folium.Popup(popup_html, max_width=280),
        tooltip=f"{r['city']} — EAQI {r['european_aqi']:.1f} ({r['label']})",
    ).add_to(layer)

layer.add_to(m)

st.components.v1.html(m.get_root().render(), height=750)

with st.expander("📋 Données (moyenne EAQI par ville pour le jour sélectionné)"):
    st.dataframe(points.sort_values("european_aqi", ascending=False), use_container_width=True)
