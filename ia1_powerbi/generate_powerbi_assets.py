import csv
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLEAN_CSV = ROOT / "data" / "clean" / "clean.csv"
OUT_DIR = ROOT / "ia1_powerbi"
TABLES_DIR = OUT_DIR / "tables"


def read_rows():
    with CLEAN_CSV.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    rows.sort(key=lambda row: (row["datetime"], row["ville"]))
    return rows


def write_csv(path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_powerbi_tables(rows):
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    dim_ville = {}
    dim_temps = {}
    fact_rows = []

    for row in rows:
        ville_key = row["ville"]
        dt = datetime.fromisoformat(row["datetime"])
        temps_key = dt.strftime("%Y%m%d%H")

        dim_ville[ville_key] = {
            "ville_key": ville_key,
            "ville": row["ville"].replace("_", " "),
            "latitude": row["latitude"],
            "longitude": row["longitude"],
        }

        dim_temps[temps_key] = {
            "temps_key": temps_key,
            "datetime": row["datetime"],
            "date": dt.date().isoformat(),
            "annee": dt.year,
            "mois": dt.month,
            "nom_mois": dt.strftime("%B"),
            "jour": dt.day,
            "heure": dt.hour,
            "jour_semaine": dt.strftime("%A"),
            "numero_jour_semaine": dt.isoweekday(),
            "weekend": "Oui" if dt.isoweekday() in (6, 7) else "Non",
        }

        fact_rows.append(
            {
                "temps_key": temps_key,
                "ville_key": ville_key,
                "aqi": row["aqi"],
                "pm10": row["pm10"],
                "pm2_5": row["pm2_5"],
                "co": row["co"],
                "no2": row["no2"],
            }
        )

    write_csv(
        TABLES_DIR / "dim_ville.csv",
        ["ville_key", "ville", "latitude", "longitude"],
        sorted(dim_ville.values(), key=lambda row: row["ville"]),
    )
    write_csv(
        TABLES_DIR / "dim_temps.csv",
        [
            "temps_key",
            "datetime",
            "date",
            "annee",
            "mois",
            "nom_mois",
            "jour",
            "heure",
            "jour_semaine",
            "numero_jour_semaine",
            "weekend",
        ],
        sorted(dim_temps.values(), key=lambda row: row["temps_key"]),
    )
    write_csv(
        TABLES_DIR / "fact_qualite_air.csv",
        ["temps_key", "ville_key", "aqi", "pm10", "pm2_5", "co", "no2"],
        fact_rows,
    )


def write_dax():
    dax = """-- Mesures DAX a creer dans Power BI

AQI moyen = AVERAGE(fact_qualite_air[aqi])

AQI maximum = MAX(fact_qualite_air[aqi])

PM10 moyen = AVERAGE(fact_qualite_air[pm10])

PM2.5 moyen = AVERAGE(fact_qualite_air[pm2_5])

CO moyen = AVERAGE(fact_qualite_air[co])

NO2 moyen = AVERAGE(fact_qualite_air[no2])

Nombre de mesures = COUNTROWS(fact_qualite_air)

Jours couverts = DISTINCTCOUNT(dim_temps[date])

Villes suivies = DISTINCTCOUNT(dim_ville[ville])

Pic AQI Dakar =
CALCULATE(
    [AQI maximum],
    dim_ville[ville] = "Dakar"
)

Ville la plus exposee =
VAR Classement =
    TOPN(
        1,
        ADDCOLUMNS(VALUES(dim_ville[ville]), "AQI", [AQI moyen]),
        [AQI],
        DESC
    )
RETURN
    CONCATENATEX(Classement, dim_ville[ville])

Ville la plus favorable =
VAR Classement =
    TOPN(
        1,
        ADDCOLUMNS(VALUES(dim_ville[ville]), "AQI", [AQI moyen]),
        [AQI],
        ASC
    )
RETURN
    CONCATENATEX(Classement, dim_ville[ville])
"""
    (OUT_DIR / "mesures_powerbi.dax").write_text(dax, encoding="utf-8")


def write_power_query():
    query = f"""// Requete Power Query optionnelle si tu veux importer directement le clean.csv
// Remplace le chemin si le projet est deplace.

let
    Source = Csv.Document(
        File.Contents("{str(CLEAN_CSV).replace(chr(92), chr(92) + chr(92))}"),
        [Delimiter=",", Columns=9, Encoding=65001, QuoteStyle=QuoteStyle.None]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(
        PromotedHeaders,
        {{
            {{"ville", type text}},
            {{"latitude", type number}},
            {{"longitude", type number}},
            {{"datetime", type datetime}},
            {{"aqi", Int64.Type}},
            {{"pm10", type number}},
            {{"pm2_5", type number}},
            {{"co", type number}},
            {{"no2", type number}}
        }}
    ),
    AddedDate = Table.AddColumn(ChangedTypes, "date", each Date.From([datetime]), type date),
    AddedHour = Table.AddColumn(AddedDate, "heure", each Time.Hour(Time.From([datetime])), Int64.Type),
    AddedWeekend = Table.AddColumn(AddedHour, "weekend", each if Date.DayOfWeek([date], Day.Monday) >= 5 then "Oui" else "Non", type text)
in
    AddedWeekend
"""
    (OUT_DIR / "power_query_clean.m").write_text(query, encoding="utf-8")


def write_guide(rows):
    cities = sorted({row["ville"].replace("_", " ") for row in rows})
    period_start = min(row["datetime"] for row in rows)
    period_end = max(row["datetime"] for row in rows)
    duplicates = len(rows) - len({(row["ville"], row["datetime"]) for row in rows})

    guide = f"""# IA1 Power BI - Guide de realisation

## Source de donnees

- Projet: SquadAnalytics DONNEES2
- Fichier source: `data/clean/clean.csv`
- Tables Power BI pretes: `ia1_powerbi/tables/`
- Periode: `{period_start}` a `{period_end}`
- Lignes: `{len(rows)}`
- Villes: `{", ".join(cities)}`
- Doublons ville + heure: `{duplicates}`

## Import dans Power BI Desktop

1. Ouvre Power BI Desktop.
2. Clique sur **Obtenir des donnees > Texte/CSV**.
3. Importe ces trois fichiers:
   - `ia1_powerbi/tables/fact_qualite_air.csv`
   - `ia1_powerbi/tables/dim_ville.csv`
   - `ia1_powerbi/tables/dim_temps.csv`
4. Dans **Modele**, cree les relations:
   - `fact_qualite_air[ville_key]` vers `dim_ville[ville_key]`
   - `fact_qualite_air[temps_key]` vers `dim_temps[temps_key]`
5. Mets les deux relations en cardinalite plusieurs-a-un, filtre simple depuis les dimensions vers la table de faits.
6. Va dans **Modelisation > Nouvelle mesure** et colle les mesures du fichier `ia1_powerbi/mesures_powerbi.dax`.

## Pages conseillees du rapport

### Page 1 - Vue globale

- Cartes KPI:
  - `Nombre de mesures`
  - `Villes suivies`
  - `Jours couverts`
  - `AQI moyen`
- Courbe:
  - Axe X: `dim_temps[date]`
  - Legende: `dim_ville[ville]`
  - Valeur: `AQI moyen`
- Histogramme:
  - Axe Y: `dim_ville[ville]`
  - Axe X: `AQI moyen`
  - Tri decroissant par `AQI moyen`

### Page 2 - Comparaison polluants

- Histogrammes groupes ou matrice avec:
  - Lignes: `dim_ville[ville]`
  - Valeurs: `PM10 moyen`, `PM2.5 moyen`, `CO moyen`, `NO2 moyen`
- Segment:
  - `dim_temps[date]`
  - `dim_ville[ville]`

### Page 3 - Analyse horaire

- Courbe ou colonnes:
  - Axe X: `dim_temps[heure]`
  - Legende: `dim_ville[ville]`
  - Valeur: `AQI moyen`
- Carte ou texte:
  - `Ville la plus exposee`
  - `Ville la plus favorable`

## Insights a dire dans la video

- Dakar a l'AQI moyen le plus eleve sur la periode: environ 82.
- Antananarivo a l'AQI moyen le plus faible: environ 24,6.
- Le pic observe atteint 181 a Dakar le 17 mai 2026 a 09h.
- Le dataset est propre pour l'analyse: 11 005 lignes et 0 doublon ville + heure.

## Rendu IA1

Email: `evaluation@databridge.mg`

Objet: `IA1 - STD - Livrables`

Pieces a envoyer:

- Video de presentation Power BI, 3 minutes maximum.
- Fichier `.pbix` Power BI si possible.
- Notebook `ia1/IA1_analyse_aqi.ipynb`.
- Captures d'ecran Power BI si tu n'as pas publie le rapport.
"""
    (OUT_DIR / "GUIDE_POWERBI_IA1.md").write_text(guide, encoding="utf-8")


def main():
    OUT_DIR.mkdir(exist_ok=True)
    rows = read_rows()
    build_powerbi_tables(rows)
    write_dax()
    write_power_query()
    write_guide(rows)
    print(f"Assets Power BI generes dans: {OUT_DIR}")


if __name__ == "__main__":
    main()
