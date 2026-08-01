import os
import glob
import json
import requests
import pandas as pd
from datetime import datetime

VILLES = {
    "Paris": {"lat": 48.8566, "lon": 2.3522},
    "Antananarivo": {"lat": -18.8792, "lon": 47.5079},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503},
    "New_York": {"lat": 40.7128, "lon": -74.0060},
    "Dakar": {"lat": 14.6937, "lon": -17.4441}
}

os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/clean", exist_ok=True)

print("1️⃣ Collecte des données AQI à l'instant T...")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

for ville, coords in VILLES.items():
   
    url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality?"
        f"latitude={coords['lat']}&longitude={coords['lon']}&"
        f"hourly=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,european_aqi&"
        f"current=european_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide&"
        f"past_days=1&forecast_days=1&timezone=auto"
    )
    res = requests.get(url)
    if res.status_code == 200:
        file_path = f"data/raw/{ville}_{timestamp}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(res.json(), f, indent=4)

print("2️⃣ Mise à jour de clean.csv...")

all_rows = []
raw_files = glob.glob("data/raw/*.json")

for file in raw_files:
    with open(file, "r", encoding="utf-8") as f:
        content = json.load(f)
        
        lat = content.get("latitude")
        lon = content.get("longitude")
        
        ville_name = "Inconnue"
        for v, coords in VILLES.items():
            if abs(coords["lat"] - lat) < 0.1 and abs(coords["lon"] - lon) < 0.1:
                ville_name = v
                break

        hourly = content.get("hourly", {})
        times = hourly.get("time", [])
        
        for i in range(len(times)):
            dt_str = times[i]
            dt_obj = datetime.fromisoformat(dt_str)
            if dt_obj <= datetime.now():
                all_rows.append({
                    "ville": ville_name,
                    "latitude": lat,
                    "longitude": lon,
                    "datetime": dt_str,
                    "aqi": hourly.get("european_aqi", [None])[i],
                    "pm10": hourly.get("pm10", [None])[i],
                    "pm2_5": hourly.get("pm2_5", [None])[i],
                    "co": hourly.get("carbon_monoxide", [None])[i],
                    "no2": hourly.get("nitrogen_dioxide", [None])[i]
                })

df = pd.DataFrame(all_rows)

df.dropna(subset=["aqi"], inplace=True)
df.drop_duplicates(subset=["ville", "datetime"], keep="last", inplace=True)
df.sort_values(by=["datetime", "ville"], inplace=True)

clean_path = "data/clean/clean.csv"
df.to_csv(clean_path, index=False)
print(f"✅ {len(df)} lignes à jour enregistrées dans {clean_path}")