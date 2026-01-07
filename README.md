# 🌍 Air Quality ETL — Europe Cities

Pipeline **ETL complète sur Google Cloud Platform (GCP)** permettant de collecter, transformer, stocker et visualiser la **qualité de l’air dans les villes européennes**.

Le projet couvre **toute la chaîne data** : API → Cloud Storage → Cloud Functions → BigQuery → Looker Studio / Streamlit.

---

## 🎯 Objectifs du projet

- Collecter quotidiennement les données de pollution de l’air
- Centraliser les données pour analyse historique
- Visualiser la pollution par ville et par pays
- Fournir une solution **scalable, automatisée et exploitable métier**

---

## 🌫️ Pourquoi ce projet est important ?

La pollution de l’air est un enjeu majeur pour :

- la santé publique
- les collectivités territoriales
- les entreprises (mobilité, immobilier, santé)
- les citoyens

Cette solution permet :

- de comparer la pollution entre villes européennes
- de suivre l’évolution temporelle
- d’identifier des zones à risque
- de proposer des indicateurs environnementaux commercialisables

---

## 🏗️ Architecture globale

   Cloud Scheduler
          |
          v
Cloud Function EXTRACT
(Open-Meteo API + GeoNames)
          |
          v
Cloud Storage (RAW JSONL.GZ)
          |
          v
Cloud Function LOAD
(Transformation & agrégation)
          |
          v
BigQuery
(air_quality_history)
          |
          v
Looker Studio / Streamlit
(Dashboards & cartes)


---

## 📦 Sources de données

### 1️⃣ Open-Meteo – Air Quality API

API publique fournissant des données horaires :

- PM10
- PM2.5
- CO (monoxyde de carbone)
- NO₂
- SO₂
- O₃
- European AQI

🔗 https://open-meteo.com/en/docs/air-quality-api

---

### 2️⃣ GeoNames — Cities Database

Fichier utilisé pour référencer les villes :

cities15000.zip

Source officielle :  
🔗 https://download.geonames.org/export/dump/cities15000.zip

Le fichier est stocké dans **Google Cloud Storage** et contient :

- nom de la ville
- latitude / longitude
- code pays
- population

**Filtrage appliqué dans l’ETL :**

- uniquement les pays européens
- uniquement les villes avec **population ≥ 100 000 habitants**

---

## 🔁 Pipeline ETL

### 🔹 STEP 1 — EXTRACT

**Cloud Function 1**

- Lit la liste des villes depuis GeoNames (ZIP)
- Filtre les villes européennes ≥ 100k habitants
- Appelle l’API Open-Meteo pour chaque ville
- Stocke les données brutes dans GCS

**Sortie :**

gs://gcs-airquality/raw/YYYY-MM-DD/<run_id>.jsonl.gz

**Variables d’environnement :**

- `PROJECT_ID`
- `BUCKET_NAME`
- `BQ_RUNS_TABLE`
- `MIN_POPULATION=100000`
- `THREADS=25`

---

### 🔹 STEP 2 — LOAD

**Cloud Function 2**

- Récupère le fichier RAW du jour
- Décompresse le JSONL.GZ
- Agrège les données horaires en moyennes journalières
- Charge les données dans BigQuery
- Garantit l’idempotence (suppression de la date avant insert)

---

## 🗂️ Stockage des données

### 📁 Google Cloud Storage

gcs-airquality/
├── raw/
│ └── YYYY-MM-DD/
│ └── <run_id>.jsonl.gz
├── prod/ (optionnel)
└── cities15000.zip


---

### 📊 BigQuery — Table principale

**Dataset :** `airq_data`  
**Table :** `air_quality_history`

| Champ | Type | Description |
|-----|------|------------|
| date | DATE | Jour de mesure |
| city | STRING | Nom de la ville |
| country | STRING | Code pays |
| european_aqi | FLOAT | AQI journalier moyen |
| pm10 | FLOAT | Moyenne PM10 |
| pm2_5 | FLOAT | Moyenne PM2.5 |
| carbon_monoxide | FLOAT | Moyenne CO |
| nitrogen_dioxide | FLOAT | Moyenne NO₂ |
| sulphur_dioxide | FLOAT | Moyenne SO₂ |
| ozone | FLOAT | Moyenne O₃ |
| population | INTEGER | Population |
| latitude | FLOAT | Latitude |
| longitude | FLOAT | Longitude |

---

## ⏰ Orchestration

**Cloud Scheduler**

- 1 job quotidien pour EXTRACT
- 1 job quotidien pour LOAD
- Exécution automatique en UTC
- Aucun déclenchement manuel requis

---

## 📈 Visualisation

### Looker Studio
- Connexion directe à BigQuery
- KPI pollution
- Comparaisons par ville / pays
- Séries temporelles

### Streamlit
- Carte interactive européenne
- Filtres par date
- Points colorés selon European AQI
- Thème sombre orienté data-viz

---

## 🎨 European AQI — Couleurs utilisées

| EAQI | Qualité | Couleur |
|----|-------|-------|
| ≤ 40 | Bon | Bleu |
| 41 – 80 | Moyen | Orange |
| > 80 | Mauvais | Rouge |

---

## 💼 Vision produit / business

Cette solution peut être :

- vendue aux collectivités locales
- intégrée à des applications météo
- utilisée par des ONG environnementales
- exploitée par des entreprises de santé ou mobilité

**Extensions possibles :**

- alertes pollution
- prévisions
- API commerciale
- segmentation géographique fine

---

## 🚀 Déploiement & Code

Repository GitHub :  
👉 https://github.com/DjeradAy/airquality-etl

Déploiement via :

- Cloud Shell
- Cloud Functions (Gen 2)
- Cloud Scheduler
- BigQuery
- Looker Studio / Streamlit

