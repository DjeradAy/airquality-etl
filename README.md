🌍 Air Quality ETL – Europe Cities
📌 Présentation du projet

Ce projet met en place une pipeline ETL complète sur Google Cloud Platform (GCP) permettant de :

Collecter quotidiennement les données de qualité de l’air pour les villes européennes

Transformer et agréger ces données

Les stocker dans BigQuery

Les visualiser via Looker Studio

🎯 Objectif métier
Fournir une solution fiable, scalable et automatisée pour analyser la pollution de l’air dans les villes européennes et permettre des usages analytiques, décisionnels et commerciaux.

🧠 Pourquoi ce projet est important ?

La pollution de l’air est un enjeu majeur pour :

🏥 la santé publique

🏛️ les collectivités locales

🏢 les entreprises

👥 les citoyens

Notre solution permet notamment :

de comparer la pollution entre villes

de suivre son évolution dans le temps

d’identifier des zones à risque

de vendre des indicateurs environnementaux à des acteurs publics ou privés

🏗️ Architecture globale
┌──────────────────┐
│ Cloud Scheduler  │
└─────────┬────────┘
          │ (HTTP)
          ▼
┌────────────────────────┐
│ Cloud Function EXTRACT │
│ - Open-Meteo API       │
│ - GeoNames cities      │
└─────────┬──────────────┘
          │
          ▼
┌────────────────────────┐
│ Cloud Storage (GCS)    │
│ raw/YYYY-MM-DD/        │
│ JSONL.GZ               │
└─────────┬──────────────┘
          │
          ▼
┌────────────────────────┐
│ Cloud Function LOAD    │
│ Transform & Aggregate  │
└─────────┬──────────────┘
          │
          ▼
┌────────────────────────┐
│ BigQuery               │
│ air_quality_history    │
└─────────┬──────────────┘
          │
          ▼
┌────────────────────────┐
│ Looker Studio          │
│ Dashboards & Maps      │
└────────────────────────┘
📦 Sources de données
1️⃣ Open-Meteo – Air Quality API

API publique utilisée pour récupérer les données horaires de pollution :

PM10

PM2.5

CO (monoxyde de carbone)

NO₂

SO₂

O₃

European AQI

📎 Documentation officielle :
https://open-meteo.com/en/docs/air-quality-api

2️⃣ GeoNames – Cities Database (ZIP)

Nous utilisons la base GeoNames cities15000.zip pour obtenir la liste des villes.

Source officielle :
👉 https://download.geonames.org/export/dump/cities15000.zip

Le fichier est stocké dans Google Cloud Storage

Il contient toutes les villes mondiales avec :

latitude

longitude

pays

population

🎯 Filtrage appliqué dans la Cloud Function EXTRACT :

uniquement les pays européens

uniquement les villes avec population ≥ 100 000 habitants

📁 Exemple de stockage :
gs://gcs-airquality/cities15000.zip
🔁 Pipeline ETL
🔹 STEP 1 – EXTRACT (Cloud Function 1)

📂 cloud_functions/extract/main.py

Rôle :

Charger la liste des villes depuis GeoNames (ZIP)

Filtrer les villes européennes ≥ 100k habitants

Appeler l’API Open-Meteo pour chaque ville

Sauvegarder les données brutes dans GCS

Sortie :
gs://gcs-airquality/raw/YYYY-MM-DD/<run_id>.jsonl.gz
Variables d’environnement :
PROJECT_ID
BUCKET_NAME
BQ_RUNS_TABLE
MIN_POPULATION=100000
THREADS=25
🔹 STEP 2 – LOAD (Cloud Function 2)

📂 cloud_functions/load/main.py

Rôle :

Lire le dernier fichier RAW du jour

Décompresser le fichier JSONL.GZ

Transformer les données horaires en agrégats journaliers

Charger les données dans BigQuery

Garantir l’idempotence (suppression des données du jour avant insertion)

🗃️ Stockage des données
📁 Google Cloud Storage
gcs-airquality/
├── raw/
│   └── 2026-01-06/
│       └── <run_id>.jsonl.gz
├── prod/        # (futures évolutions)
└── cities15000.zip
📊 BigQuery
Table principale : airq_data.air_quality_history
Champ	Type	Description
date	DATE	Jour de mesure
city	STRING	Nom de la ville
country	STRING	Code pays
pm10	FLOAT	Moyenne journalière
pm2_5	FLOAT	Moyenne journalière
carbon_monoxide	FLOAT	Moyenne
nitrogen_dioxide	FLOAT	Moyenne
sulphur_dioxide	FLOAT	Moyenne
ozone	FLOAT	Moyenne
european_aqi	FLOAT	AQI moyen
population	INTEGER	Population
latitude	FLOAT	Latitude
longitude	FLOAT	Longitude
⏰ Orchestration – Cloud Scheduler

✅ 1 job quotidien pour EXTRACT

✅ 1 job quotidien pour LOAD

🌍 Fuseau horaire : UTC

🤖 Exécution automatique sans intervention humaine

📈 Visualisation – Looker Studio

Connexion directe à BigQuery pour :

🗺️ cartes géographiques (latitude / longitude)

📊 évolution temporelle de la pollution

🌍 comparaisons entre villes et pays

📈 indicateurs environnementaux

🎯 Pourquoi BigQuery et pas GCS ?

requêtes rapides

agrégations natives

intégration directe avec Looker Studio

💼 Vision produit / business

Cette solution peut être :

vendue à des collectivités

intégrée dans des applications météo

utilisée par des ONG

exploitée par des entreprises de mobilité ou de santé

Extensions possibles :

alertes pollution en temps réel

prévisions de qualité de l’air

segmentation par quartiers

API commerciale

🚀 Déploiement

Tout le code est versionné sur GitHub :
👉 https://github.com/DjeradAy/airquality-etl

Déploiement effectué via :

Cloud Shell

Cloud Functions

Cloud Scheduler

BigQuery
