import os
import requests
import json
from datetime import datetime, timedelta

VILLES = {
    "Paris": {"lat": 48.8566, "lon": 2.3522},
    "Antananarivo": {"lat": -18.8792, "lon": 47.5079},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503},
    "New_York": {"lat": 40.7128, "lon": -74.0060},
    "Dakar": {"lat": 14.6937, "lon": -17.4441}
}

os.makedirs("data/raw", exist_ok=True)

end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

print(f"🚀 Téléchargement des données du {start_date} au {end_date}...")

for ville, coords in VILLES.items():
    url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality?"
        f"latitude={coords['lat']}&longitude={coords['lon']}&"
        f"hourly=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,european_aqi&"
        f"start_date={start_date}&end_date={end_date}&timezone=auto"
    )
    
    res = requests.get(url)
    if res.status_code == 200:
        filename = f"data/raw/backfill_3mois_{ville}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(res.json(), f, indent=4)
        print(f"✅ 3 mois de données récupérés pour {ville}")
    else:
        print(f"❌ Erreur pour {ville}: {res.status_code}")

print("✨ Téléchargement terminé !")