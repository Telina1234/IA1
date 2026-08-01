# 🌍 AQI Data Pipeline & Data Warehouse — SquadAnalytics

Projet de collecte, traitement et modélisation des données de qualité de l'air (AQI) en temps réel pour 5 villes à travers le monde.

---

## 📍 Villes Couvertes

Le pipeline collecte les données de qualité de l'air pour 5 villes réparties sur différents continents :

| Ville | Pays | Latitude | Longitude |
| :--- | :--- | :--- | :--- |
| **Paris** | France | `48.8566` | `2.3522` |
| **Antananarivo** | Madagascar | `-18.8792` | `47.5079` |
| **Tokyo** | Japon | `35.6762` | `139.6503` |
| **New York** | États-Unis | `40.7128` | `-74.0060` |
| **Dakar** | Sénégal | `14.6937` | `-17.4441` |

---

## 📜 Contrat de Données (`data/clean/clean.csv`)

Le fichier `clean.csv` rassemble l'ensemble de l'historique nettoyé, trié par ordre chronologique et sans doublons.

### Description des colonnes et unités :

| Colonne | Type | Unité / Format | Description |
| :--- | :--- | :--- | :--- |
| `datetime` | ISO8601 String | `YYYY-MM-DDTHH:MM` | Horodatage de la mesure |
| `ville` | String | N/A | Nom de la ville |
| `latitude` | Float | Degrés décimaux | Latitude de la station |
| `longitude` | Float | Degrés décimaux | Longitude de la station |
| `aqi` | Integer | Indice European AQI (0-500) | Indice de qualité de l'air européen |
| `pm10` | Float | µg/m³ | Particules en suspension < 10µm |
| `pm2_5` | Float | µg/m³ | Particules fines < 2.5µm |
| `co` | Float | µg/m³ | Monoxyde de carbone |
| `no2` | Float | µg/m³ | Dioxyde d'azote |

---

## 🏛️ Schéma du Data Warehouse

Le Data Warehouse est modélisé selon un **schéma en étoile** pour optimiser les requêtes analytiques.

### 1. Table de Faits : `fact_qualite_air`
* **Clés étrangères / Jointures :** `datetime`, `ville`
* **Mesures analytiques :** `aqi`, `pm10`, `pm2_5`, `co`, `no2`

### 2. Dimension Ville : `dim_ville`
* **Clé primaire :** `ville`
* **Attributs :** `latitude`, `longitude`

### 3. Dimension Temps : `dim_temps`
* **Clé primaire :** `datetime`
* **Attributs :** `date`, `annee`, `mois`, `jour`, `heure`

---

## 📅 Période Couverte & Informations sur la Base

* **Période couverte :** Du 01 Mai 2026 au jour présent (3 mois glissants d'historique complet via `backfill.py` + mises à jour horaires).
* **Trous connus :** Aucun trou majeur détecté. Les éventuelles micro-coupures de l'API Open-Meteo sont gérées lors du rebuild du fichier clean.
* **Fichier de base de données :** `data/warehouse.db` (SQLite).

### 🔌 Connexion à la base SQLite en Python :
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("data/warehouse.db")
df_facts = pd.read_sql_query("SELECT * FROM fact_qualite_air LIMIT 10", conn)
print(df_facts)
conn.close()