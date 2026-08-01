import sqlite3
import pandas as pd

CLEAN_CSV = "data/clean/clean.csv"
DB_FILE = "data/warehouse.db"

def build_warehouse():
    print("🚀 Alimentation du Data Warehouse...")
    df = pd.read_csv(CLEAN_CSV)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    df['datetime'] = pd.to_datetime(df['datetime'])
    dim_time = df[['datetime']].drop_duplicates().copy()
    dim_time['date'] = dim_time['datetime'].dt.date
    dim_time['annee'] = dim_time['datetime'].dt.year
    dim_time['mois'] = dim_time['datetime'].dt.month
    dim_time['jour'] = dim_time['datetime'].dt.day
    dim_time['heure'] = dim_time['datetime'].dt.hour
    dim_time.to_sql('dim_temps', conn, if_exists='replace', index=False)

    dim_ville = df[['ville', 'latitude', 'longitude']].drop_duplicates().copy()
    dim_ville.to_sql('dim_ville', conn, if_exists='replace', index=False)

    fact_aqi = df[['datetime', 'ville', 'aqi', 'pm10', 'pm2_5', 'co', 'no2']].copy()
    fact_aqi['datetime'] = fact_aqi['datetime'].astype(str)
    fact_aqi.to_sql('fact_qualite_air', conn, if_exists='replace', index=False)

    conn.close()
    print("✅ Base de données à jour dans data/warehouse.db !")

if __name__ == "__main__":
    build_warehouse()