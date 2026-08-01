import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLEAN_CSV = ROOT / "data" / "clean" / "clean.csv"
OUT_DIR = ROOT / "ia1"
DASHBOARD = OUT_DIR / "dashboard_aqi_ia1.html"
NOTEBOOK = OUT_DIR / "IA1_analyse_aqi.ipynb"
RENDU = OUT_DIR / "README_RENDU_IA1.md"

POLLUTANTS = ["pm10", "pm2_5", "co", "no2"]
TREND_METRICS = ["aqi", "pm10", "pm2_5", "no2"]
CITY_LABELS = {
    "Antananarivo": "Antananarivo",
    "Dakar": "Dakar",
    "New_York": "New York",
    "Paris": "Paris",
    "Tokyo": "Tokyo",
}


def parse_float(value):
    try:
        if value == "":
            return None
        parsed = float(value)
        if math.isnan(parsed):
            return None
        return parsed
    except (TypeError, ValueError):
        return None


def avg(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def round_or_none(value, digits=2):
    return None if value is None else round(value, digits)


def read_rows():
    with CLEAN_CSV.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = []
        for item in reader:
            dt = datetime.fromisoformat(item["datetime"])
            row = {
                "ville": item["ville"],
                "city": CITY_LABELS.get(item["ville"], item["ville"]),
                "latitude": parse_float(item["latitude"]),
                "longitude": parse_float(item["longitude"]),
                "datetime": item["datetime"],
                "date": dt.date().isoformat(),
                "hour": dt.hour,
                "weekday": dt.strftime("%A"),
                "aqi": parse_float(item["aqi"]),
            }
            for pollutant in POLLUTANTS:
                row[pollutant] = parse_float(item[pollutant])
            rows.append(row)
    rows.sort(key=lambda r: (r["datetime"], r["ville"]))
    return rows


def build_payload(rows):
    cities = sorted({row["ville"] for row in rows})
    dates = sorted({row["date"] for row in rows})
    city_stats = []
    daily_by_city_metric = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    hourly_by_city = defaultdict(lambda: defaultdict(list))
    pollutant_by_city = defaultdict(lambda: defaultdict(list))
    quality_buckets = defaultdict(lambda: defaultdict(int))

    for row in rows:
        for metric in TREND_METRICS:
            daily_by_city_metric[metric][row["ville"]][row["date"]].append(row[metric])
        hourly_by_city[row["ville"]][row["hour"]].append(row["aqi"])
        for pollutant in POLLUTANTS:
            pollutant_by_city[row["ville"]][pollutant].append(row[pollutant])

        aqi = row["aqi"]
        if aqi is None:
            bucket = "Indisponible"
        elif aqi <= 20:
            bucket = "Bonne"
        elif aqi <= 40:
            bucket = "Moyenne"
        elif aqi <= 60:
            bucket = "Degradee"
        elif aqi <= 80:
            bucket = "Mauvaise"
        elif aqi <= 100:
            bucket = "Tres mauvaise"
        else:
            bucket = "Extreme"
        quality_buckets[row["ville"]][bucket] += 1

    for city in cities:
        subset = [row for row in rows if row["ville"] == city]
        aqi_values = [row["aqi"] for row in subset if row["aqi"] is not None]
        max_row = max(subset, key=lambda r: -1 if r["aqi"] is None else r["aqi"])
        city_stats.append(
            {
                "ville": city,
                "city": CITY_LABELS.get(city, city),
                "records": len(subset),
                "latitude": round_or_none(subset[0]["latitude"], 4),
                "longitude": round_or_none(subset[0]["longitude"], 4),
                "avg_aqi": round_or_none(avg(aqi_values), 2),
                "max_aqi": round_or_none(max(aqi_values), 2),
                "peak_datetime": max_row["datetime"],
                "avg_pm10": round_or_none(avg(row["pm10"] for row in subset), 2),
                "avg_pm2_5": round_or_none(avg(row["pm2_5"] for row in subset), 2),
                "avg_co": round_or_none(avg(row["co"] for row in subset), 2),
                "avg_no2": round_or_none(avg(row["no2"] for row in subset), 2),
            }
        )

    daily_series = {
        metric: {
            city: [
                {"date": date, "value": round_or_none(avg(daily_by_city_metric[metric][city][date]), 2)}
                for date in dates
                if daily_by_city_metric[metric][city][date]
            ]
            for city in cities
        }
        for metric in TREND_METRICS
    }
    hourly_series = {
        city: [
            {"hour": hour, "aqi": round_or_none(avg(hourly_by_city[city][hour]), 2)}
            for hour in range(24)
        ]
        for city in cities
    }
    pollutant_summary = {
        city: {
            pollutant: round_or_none(avg(values), 2)
            for pollutant, values in pollutant_by_city[city].items()
        }
        for city in cities
    }

    top_city = max(city_stats, key=lambda row: row["avg_aqi"])
    cleanest_city = min(city_stats, key=lambda row: row["avg_aqi"])
    peak_city = max(city_stats, key=lambda row: row["max_aqi"])
    period_start = min(row["datetime"] for row in rows)
    period_end = max(row["datetime"] for row in rows)

    return {
        "meta": {
            "records": len(rows),
            "cities": len(cities),
            "period_start": period_start,
            "period_end": period_end,
            "days": len(dates),
            "duplicates": len(rows) - len({(row["ville"], row["datetime"]) for row in rows}),
        },
        "cities": cities,
        "cityLabels": CITY_LABELS,
        "cityStats": city_stats,
        "dailySeries": daily_series,
        "hourlySeries": hourly_series,
        "pollutantSummary": pollutant_summary,
        "qualityBuckets": quality_buckets,
        "insights": [
            f"{CITY_LABELS.get(top_city['ville'], top_city['ville'])} affiche l'AQI moyen le plus eleve ({top_city['avg_aqi']}).",
            f"{CITY_LABELS.get(cleanest_city['ville'], cleanest_city['ville'])} est la ville la plus favorable sur la periode ({cleanest_city['avg_aqi']} en moyenne).",
            f"Le pic observe atteint {peak_city['max_aqi']} a {CITY_LABELS.get(peak_city['ville'], peak_city['ville'])} le {peak_city['peak_datetime']}.",
            "Le fichier clean respecte le contrat IA1/DONNEES2: une ligne par ville et par heure, sans doublons.",
        ],
    }


def write_dashboard(payload):
    data = json.dumps(payload, ensure_ascii=False)
    html = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard IA1 - Qualite de l'air</title>
  <style>
    :root {{
      --bg: #f6f7fb;
      --panel: #ffffff;
      --text: #172033;
      --muted: #687084;
      --line: #dfe4ee;
      --accent: #146c94;
      --accent-2: #d66f3d;
      --green: #2f8f6f;
      --yellow: #d5a11e;
      --red: #c44a4a;
      --shadow: 0 10px 30px rgba(23, 32, 51, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, Segoe UI, Roboto, Arial, sans-serif;
      line-height: 1.45;
    }}
    header {{
      padding: 28px 36px 20px;
      background: #102033;
      color: white;
    }}
    header h1 {{ margin: 0; font-size: clamp(28px, 4vw, 48px); letter-spacing: 0; }}
    header p {{ margin: 8px 0 0; max-width: 980px; color: #d7deea; font-size: 16px; }}
    main {{ padding: 24px 36px 40px; max-width: 1440px; margin: 0 auto; }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      margin-bottom: 20px;
    }}
    select, button {{
      min-height: 40px;
      border: 1px solid var(--line);
      background: white;
      color: var(--text);
      border-radius: 6px;
      padding: 8px 12px;
      font: inherit;
    }}
    button {{ cursor: pointer; }}
    button.active {{ background: var(--accent); color: white; border-color: var(--accent); }}
    .grid {{ display: grid; gap: 16px; }}
    .kpis {{ grid-template-columns: repeat(4, minmax(160px, 1fr)); margin-bottom: 16px; }}
    .cards {{ grid-template-columns: 1.25fr 0.75fr; align-items: start; }}
    .triple {{ grid-template-columns: repeat(3, minmax(0, 1fr)); margin-top: 16px; }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: 18px;
    }}
    .kpi strong {{ display: block; font-size: 28px; margin-top: 4px; }}
    .kpi span, .caption {{ color: var(--muted); font-size: 13px; }}
    h2 {{ margin: 0 0 14px; font-size: 20px; }}
    h3 {{ margin: 0 0 10px; font-size: 16px; }}
    svg {{ width: 100%; height: auto; display: block; overflow: visible; }}
    .legend {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 10px; color: var(--muted); font-size: 13px; }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 6px; }}
    .table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    .table th, .table td {{ border-bottom: 1px solid var(--line); padding: 8px; text-align: left; }}
    .table th {{ color: var(--muted); font-weight: 600; }}
    .insights {{ display: grid; gap: 10px; }}
    .insight {{ border-left: 4px solid var(--accent-2); padding: 8px 10px; background: #fff8f2; border-radius: 4px; }}
    .city-list {{ display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 10px; margin-top: 10px; }}
    .city-pill {{ border: 1px solid var(--line); border-radius: 6px; padding: 10px; background: white; }}
    .city-pill strong {{ display: block; }}
    @media (max-width: 900px) {{
      header, main {{ padding-left: 18px; padding-right: 18px; }}
      .kpis, .cards, .triple, .city-list {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Dashboard IA1 - Qualite de l'air</h1>
    <p>Analyse individuelle des donnees AQI collectees par le pipeline DONNEES2 de SquadAnalytics.</p>
  </header>
  <main>
    <section class="toolbar" aria-label="Filtres du dashboard">
      <label>Ville
        <select id="citySelect"></select>
      </label>
      <button data-metric="aqi" class="active">AQI</button>
      <button data-metric="pm10">PM10</button>
      <button data-metric="pm2_5">PM2.5</button>
      <button data-metric="no2">NO2</button>
    </section>

    <section class="grid kpis">
      <article class="panel kpi"><span>Lignes analysees</span><strong id="kpiRows"></strong></article>
      <article class="panel kpi"><span>Villes suivies</span><strong id="kpiCities"></strong></article>
      <article class="panel kpi"><span>Periode couverte</span><strong id="kpiPeriod"></strong></article>
      <article class="panel kpi"><span>Doublons ville+heure</span><strong id="kpiDup"></strong></article>
    </section>

    <section class="grid cards">
      <article class="panel">
        <h2 id="trendTitle">Evolution quotidienne</h2>
        <svg id="lineChart" viewBox="0 0 920 360" role="img"></svg>
        <div class="legend" id="lineLegend"></div>
      </article>
      <aside class="panel">
        <h2>Insights a presenter</h2>
        <div class="insights" id="insights"></div>
      </aside>
    </section>

    <section class="grid triple">
      <article class="panel">
        <h2>AQI moyen par ville</h2>
        <svg id="barChart" viewBox="0 0 480 320" role="img"></svg>
      </article>
      <article class="panel">
        <h2>Profil horaire</h2>
        <svg id="hourChart" viewBox="0 0 480 320" role="img"></svg>
        <p class="caption">Moyenne par heure de la journee pour la ville selectionnee.</p>
      </article>
      <article class="panel">
        <h2>Polluants moyens</h2>
        <svg id="pollutantChart" viewBox="0 0 480 320" role="img"></svg>
      </article>
    </section>

    <section class="panel" style="margin-top:16px">
      <h2>Comparatif des villes</h2>
      <table class="table" id="cityTable"></table>
      <div class="city-list" id="cityList"></div>
    </section>
  </main>
  <script>
    const DATA = {data};
    const COLORS = ["#146c94", "#d66f3d", "#2f8f6f", "#8a5a9e", "#d5a11e"];
    let selectedCity = DATA.cities[0];
    let selectedMetric = "aqi";
    const METRIC_LABELS = {{"aqi": "AQI", "pm10": "PM10", "pm2_5": "PM2.5", "no2": "NO2"}};

    const label = (city) => DATA.cityLabels[city] || city;
    const fmt = (value) => Number(value).toLocaleString("fr-FR", {{ maximumFractionDigits: 2 }});
    const svgEl = (name, attrs = {{}}, text = "") => {{
      const node = document.createElementNS("http://www.w3.org/2000/svg", name);
      for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
      if (text) node.textContent = text;
      return node;
    }};
    const clear = (id) => {{ document.getElementById(id).innerHTML = ""; return document.getElementById(id); }};

    function scale(value, min, max, outMin, outMax) {{
      if (max === min) return (outMin + outMax) / 2;
      return outMin + (value - min) * (outMax - outMin) / (max - min);
    }}

    function drawLineChart() {{
      const svg = clear("lineChart");
      const width = 920, height = 360, left = 60, right = 20, top = 24, bottom = 52;
      const selectedOnly = selectedMetric !== "aqi";
      const citySet = selectedOnly ? [selectedCity] : DATA.cities;
      const metricSeries = DATA.dailySeries[selectedMetric];
      const allPoints = citySet.flatMap(city => metricSeries[city]);
      const maxY = Math.max(...allPoints.map(point => point.value)) * 1.08;
      const dates = metricSeries[DATA.cities[0]].map(point => point.date);
      document.getElementById("trendTitle").textContent = `Evolution quotidienne - ${{METRIC_LABELS[selectedMetric]}}`;
      const minX = 0, maxX = dates.length - 1;
      [0, 0.25, 0.5, 0.75, 1].forEach(t => {{
        const y = top + t * (height - top - bottom);
        svg.appendChild(svgEl("line", {{ x1: left, x2: width-right, y1: y, y2: y, stroke: "#e7ebf2" }}));
        svg.appendChild(svgEl("text", {{ x: 8, y: y + 4, fill: "#687084", "font-size": 12 }}, Math.round(maxY * (1 - t))));
      }});
      citySet.forEach((city, index) => {{
        const points = metricSeries[city].map((point, i) => {{
          const x = scale(i, minX, maxX, left, width - right);
          const y = scale(point.value, 0, maxY, height - bottom, top);
          return `${{x}},${{y}}`;
        }}).join(" ");
        svg.appendChild(svgEl("polyline", {{ points, fill: "none", stroke: COLORS[index % COLORS.length], "stroke-width": 2.5 }}));
      }});
      svg.appendChild(svgEl("line", {{ x1: left, x2: width-right, y1: height-bottom, y2: height-bottom, stroke: "#b9c1d0" }}));
      svg.appendChild(svgEl("line", {{ x1: left, x2: left, y1: top, y2: height-bottom, stroke: "#b9c1d0" }}));
      svg.appendChild(svgEl("text", {{ x: left, y: height - 20, fill: "#687084", "font-size": 12 }}, dates[0]));
      svg.appendChild(svgEl("text", {{ x: width - 130, y: height - 20, fill: "#687084", "font-size": 12 }}, dates[dates.length - 1]));
      document.getElementById("lineLegend").innerHTML = citySet.map((city, index) =>
        `<span><i class="dot" style="background:${{COLORS[index % COLORS.length]}}"></i>${{label(city)}}</span>`
      ).join("");
    }}

    function drawBarChart() {{
      const svg = clear("barChart");
      const stats = [...DATA.cityStats].sort((a, b) => b.avg_aqi - a.avg_aqi);
      const max = Math.max(...stats.map(row => row.avg_aqi)) * 1.12;
      const left = 88, top = 24, barH = 34, gap = 18;
      stats.forEach((row, index) => {{
        const y = top + index * (barH + gap);
        const w = scale(row.avg_aqi, 0, max, 0, 340);
        svg.appendChild(svgEl("text", {{ x: 0, y: y + 23, fill: "#172033", "font-size": 13 }}, row.city));
        svg.appendChild(svgEl("rect", {{ x: left, y, width: w, height: barH, rx: 5, fill: row.ville === selectedCity ? "#d66f3d" : "#146c94" }}));
        svg.appendChild(svgEl("text", {{ x: left + w + 8, y: y + 22, fill: "#687084", "font-size": 13 }}, fmt(row.avg_aqi)));
      }});
    }}

    function drawHourChart() {{
      const svg = clear("hourChart");
      const points = DATA.hourlySeries[selectedCity];
      const max = Math.max(...points.map(point => point.aqi)) * 1.15;
      const left = 44, right = 18, top = 24, bottom = 42, width = 480, height = 320;
      const barW = (width - left - right) / 24 - 3;
      points.forEach(point => {{
        const x = left + point.hour * ((width - left - right) / 24);
        const h = scale(point.aqi, 0, max, 0, height - top - bottom);
        const y = height - bottom - h;
        svg.appendChild(svgEl("rect", {{ x, y, width: barW, height: h, fill: "#2f8f6f", rx: 3 }}));
      }});
      svg.appendChild(svgEl("line", {{ x1: left, x2: width-right, y1: height-bottom, y2: height-bottom, stroke: "#b9c1d0" }}));
      svg.appendChild(svgEl("text", {{ x: left, y: height - 14, fill: "#687084", "font-size": 12 }}, "0h"));
      svg.appendChild(svgEl("text", {{ x: width - 42, y: height - 14, fill: "#687084", "font-size": 12 }}, "23h"));
      svg.appendChild(svgEl("text", {{ x: 6, y: top + 8, fill: "#687084", "font-size": 12 }}, Math.round(max)));
    }}

    function drawPollutantChart() {{
      const svg = clear("pollutantChart");
      const values = DATA.pollutantSummary[selectedCity];
      const items = [
        ["PM10", values.pm10, "ug/m3"],
        ["PM2.5", values.pm2_5, "ug/m3"],
        ["CO", values.co, "ug/m3"],
        ["NO2", values.no2, "ug/m3"],
      ];
      const max = Math.max(...items.map(item => item[1])) * 1.12;
      items.forEach((item, index) => {{
        const x = 42 + index * 108;
        const h = scale(item[1], 0, max, 0, 210);
        const y = 260 - h;
        svg.appendChild(svgEl("rect", {{ x, y, width: 58, height: h, rx: 6, fill: COLORS[index] }}));
        svg.appendChild(svgEl("text", {{ x: x - 2, y: 286, fill: "#172033", "font-size": 13 }}, item[0]));
        svg.appendChild(svgEl("text", {{ x: x - 4, y: y - 8, fill: "#687084", "font-size": 12 }}, fmt(item[1])));
      }});
    }}

    function renderTable() {{
      const rows = [...DATA.cityStats].sort((a, b) => b.avg_aqi - a.avg_aqi);
      document.getElementById("cityTable").innerHTML = `
        <thead><tr><th>Ville</th><th>Lignes</th><th>AQI moyen</th><th>AQI max</th><th>Pic</th><th>PM2.5 moyen</th></tr></thead>
        <tbody>${{rows.map(row => `
          <tr><td>${{row.city}}</td><td>${{fmt(row.records)}}</td><td>${{fmt(row.avg_aqi)}}</td><td>${{fmt(row.max_aqi)}}</td><td>${{row.peak_datetime}}</td><td>${{fmt(row.avg_pm2_5)}}</td></tr>
        `).join("")}}</tbody>`;
      document.getElementById("cityList").innerHTML = rows.map(row => `
        <div class="city-pill"><strong>${{row.city}}</strong><span>${{row.latitude}}, ${{row.longitude}}</span></div>
      `).join("");
    }}

    function renderAll() {{
      const meta = DATA.meta;
      document.getElementById("kpiRows").textContent = fmt(meta.records);
      document.getElementById("kpiCities").textContent = fmt(meta.cities);
      document.getElementById("kpiPeriod").textContent = `${{meta.period_start.slice(0,10)}} -> ${{meta.period_end.slice(0,10)}}`;
      document.getElementById("kpiDup").textContent = fmt(meta.duplicates);
      document.getElementById("insights").innerHTML = DATA.insights.map(text => `<div class="insight">${{text}}</div>`).join("");
      drawLineChart();
      drawBarChart();
      drawHourChart();
      drawPollutantChart();
      renderTable();
    }}

    const select = document.getElementById("citySelect");
    select.innerHTML = DATA.cities.map(city => `<option value="${{city}}">${{label(city)}}</option>`).join("");
    select.addEventListener("change", event => {{ selectedCity = event.target.value; renderAll(); }});
    document.querySelectorAll("button[data-metric]").forEach(button => {{
      button.addEventListener("click", () => {{
        selectedMetric = button.dataset.metric;
        document.querySelectorAll("button[data-metric]").forEach(btn => btn.classList.remove("active"));
        button.classList.add("active");
        renderAll();
      }});
    }});
    renderAll();
  </script>
</body>
</html>
"""
    DASHBOARD.write_text(html, encoding="utf-8")


def write_notebook(payload):
    markdown_intro = """# IA1 - Analyse individuelle AQI

Ce notebook analyse le fichier `data/clean/clean.csv` produit par le pipeline DONNEES2 de SquadAnalytics. L'objectif est de preparer les visualisations et les insights presentes dans le dashboard IA1.
"""
    code_load = """from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path.cwd()
if not (ROOT / "data" / "clean" / "clean.csv").exists():
    ROOT = ROOT.parent
CLEAN_CSV = ROOT / "data" / "clean" / "clean.csv"
WAREHOUSE = ROOT / "data" / "warehouse.db"

df = pd.read_csv(CLEAN_CSV, parse_dates=["datetime"])
df = df.sort_values(["datetime", "ville"]).reset_index(drop=True)
df.head()
"""
    code_quality = """print("Nombre de lignes:", len(df))
print("Villes:", sorted(df["ville"].unique()))
print("Periode:", df["datetime"].min(), "->", df["datetime"].max())
print("Doublons ville+heure:", df.duplicated(["ville", "datetime"]).sum())

df.isna().sum()
"""
    code_city = """city_summary = (
    df.groupby("ville")
    .agg(
        lignes=("aqi", "size"),
        aqi_moyen=("aqi", "mean"),
        aqi_max=("aqi", "max"),
        pm10_moyen=("pm10", "mean"),
        pm25_moyen=("pm2_5", "mean"),
        co_moyen=("co", "mean"),
        no2_moyen=("no2", "mean"),
    )
    .round(2)
    .sort_values("aqi_moyen", ascending=False)
)
city_summary
"""
    code_daily = """daily_aqi = (
    df.assign(date=df["datetime"].dt.date)
    .groupby(["date", "ville"], as_index=False)["aqi"]
    .mean()
)

ax = daily_aqi.pivot(index="date", columns="ville", values="aqi").plot(
    figsize=(12, 5),
    title="Evolution quotidienne de l'AQI moyen par ville",
)
ax.set_xlabel("Date")
ax.set_ylabel("AQI moyen")
"""
    code_hour = """hourly_profile = (
    df.assign(heure=df["datetime"].dt.hour)
    .groupby(["heure", "ville"], as_index=False)["aqi"]
    .mean()
)

ax = hourly_profile.pivot(index="heure", columns="ville", values="aqi").plot(
    figsize=(12, 5),
    title="Profil horaire moyen de l'AQI",
)
ax.set_xlabel("Heure")
ax.set_ylabel("AQI moyen")
"""
    code_sql = """conn = sqlite3.connect(WAREHOUSE)
query = '''
SELECT f.ville, ROUND(AVG(f.aqi), 2) AS aqi_moyen, MAX(f.aqi) AS aqi_max, COUNT(*) AS lignes
FROM fact_qualite_air f
GROUP BY f.ville
ORDER BY aqi_moyen DESC;
'''
pd.read_sql_query(query, conn)
"""
    markdown_insights = "\n".join(["## Insights principaux", *[f"- {item}" for item in payload["insights"]]])
    cells = [
        {"cell_type": "markdown", "metadata": {}, "source": markdown_intro.splitlines(True)},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": code_load.splitlines(True)},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": code_quality.splitlines(True)},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": code_city.splitlines(True)},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": code_daily.splitlines(True)},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": code_hour.splitlines(True)},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": code_sql.splitlines(True)},
        {"cell_type": "markdown", "metadata": {}, "source": markdown_insights.splitlines(True)},
    ]
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8")


def write_rendu(payload):
    lines = [
        "# Rendu IA1 individuel",
        "",
        "## Fichiers a envoyer",
        "",
        "- Video de presentation du dashboard, 3 minutes maximum.",
        "- `ia1/dashboard_aqi_ia1.html` comme dashboard local, ou des captures d'ecran de ce dashboard si aucun lien public n'est disponible.",
        "- `ia1/IA1_analyse_aqi.ipynb` comme notebook d'analyse.",
        "- Lien vers le repo GitHub du projet DONNEES2 si tu veux donner le contexte des donnees.",
        "",
        "## Script video conseille",
        "",
        "1. Ouvrir le dashboard et presenter la periode couverte, les 5 villes et les 11 005 lignes sans doublons.",
        "2. Montrer l'evolution quotidienne de l'AQI et expliquer la comparaison entre villes.",
        "3. Selectionner Dakar puis Antananarivo pour montrer le contraste entre la ville la plus exposee et la plus favorable.",
        "4. Montrer le profil horaire et les polluants moyens pour prouver que le dashboard est interactif.",
        "5. Ouvrir rapidement le notebook pour montrer que les insights viennent de l'analyse du fichier clean.",
        "",
        "## Email de rendu",
        "",
        "Destinataire: `evaluation@databridge.mg`",
        "",
        "Objet: `IA1 - STD - Livrables`",
        "",
        "Contenu a adapter:",
        "",
        "```text",
        "Bonjour,",
        "",
        "Veuillez trouver ci-joint mes livrables pour le projet IA1 individuel:",
        "- la video de presentation du dashboard;",
        "- le fichier notebook utilise pour l'analyse;",
        "- les captures d'ecran du dashboard / ou le lien public du dashboard si disponible.",
        "",
        "Nom: [TON NOM]",
        "STD: [TON STD]",
        "Dashboard: [LIEN PUBLIC OU mention: fichier HTML/captures jointes]",
        "Notebook: IA1_analyse_aqi.ipynb",
        "",
        "Cordialement,",
        "```",
        "",
        "## Insights repris dans le dashboard",
        "",
    ]
    lines.extend([f"- {item}" for item in payload["insights"]])
    RENDU.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    OUT_DIR.mkdir(exist_ok=True)
    rows = read_rows()
    payload = build_payload(rows)
    write_dashboard(payload)
    write_notebook(payload)
    write_rendu(payload)
    print(f"Dashboard: {DASHBOARD}")
    print(f"Notebook: {NOTEBOOK}")
    print(f"Guide rendu: {RENDU}")


if __name__ == "__main__":
    main()
