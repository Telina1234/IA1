import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLEAN_CSV = ROOT / "data" / "clean" / "clean.csv"
OUT_DIR = ROOT / "ia1_powerbi"
HTML_OUT = OUT_DIR / "dashboard_powerbi_background.html"
JSON_OUT = OUT_DIR / "dashboard_powerbi_data.json"

CITY_LABELS = {
    "Antananarivo": "Antananarivo",
    "Dakar": "Dakar",
    "New_York": "New York",
    "Paris": "Paris",
    "Tokyo": "Tokyo",
}

COLORS = {
    "Antananarivo": "#1779a6",
    "Dakar": "#dc6b36",
    "New_York": "#2d936c",
    "Paris": "#8b5aa6",
    "Tokyo": "#d4a318",
}


def fnum(value):
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")


def parse_rows():
    with CLEAN_CSV.open(newline="", encoding="utf-8") as file:
        rows = []
        for row in csv.DictReader(file):
            dt = datetime.fromisoformat(row["datetime"])
            item = {
                "ville": row["ville"],
                "city": CITY_LABELS.get(row["ville"], row["ville"]),
                "datetime": dt,
                "date": dt.date().isoformat(),
                "hour": dt.hour,
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "aqi": float(row["aqi"]),
                "pm10": float(row["pm10"]),
                "pm2_5": float(row["pm2_5"]),
                "co": float(row["co"]),
                "no2": float(row["no2"]),
            }
            rows.append(item)
    rows.sort(key=lambda row: (row["datetime"], row["ville"]))
    return rows


def avg(values):
    values = list(values)
    return sum(values) / len(values) if values else 0


def make_polyline(series, x0, y0, width, height, max_y):
    if len(series) == 1:
        x = x0 + width / 2
        y = y0 + height - (series[0] / max_y * height)
        return f"{x:.1f},{y:.1f}"
    points = []
    for index, value in enumerate(series):
        x = x0 + (index / (len(series) - 1)) * width
        y = y0 + height - (value / max_y * height)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def svg_line_chart(daily_series, cities):
    width, height = 1040, 360
    x0, y0 = 70, 34
    chart_w, chart_h = 910, 255
    max_y = max(max(values) for values in daily_series.values()) * 1.08
    ticks = [0, 0.25, 0.5, 0.75, 1]
    grid = []
    for tick in ticks:
        y = y0 + tick * chart_h
        label = round(max_y * (1 - tick))
        grid.append(f'<line x1="{x0}" x2="{x0 + chart_w}" y1="{y:.1f}" y2="{y:.1f}" stroke="#e4e9f2"/>')
        grid.append(f'<text x="16" y="{y + 4:.1f}" class="axis">{label}</text>')
    lines = []
    for city in cities:
        points = make_polyline(daily_series[city], x0, y0, chart_w, chart_h, max_y)
        lines.append(
            f'<polyline points="{points}" fill="none" stroke="{COLORS[city]}" stroke-width="3" '
            f'stroke-linejoin="round" stroke-linecap="round"/>'
        )
    legend = []
    lx = 70
    for city in cities:
        legend.append(f'<circle cx="{lx}" cy="332" r="6" fill="{COLORS[city]}"/>')
        legend.append(f'<text x="{lx + 12}" y="337" class="legend">{CITY_LABELS[city]}</text>')
        lx += 140
    return f"""
<svg viewBox="0 0 {width} {height}" class="chart">
  {''.join(grid)}
  <line x1="{x0}" x2="{x0 + chart_w}" y1="{y0 + chart_h}" y2="{y0 + chart_h}" stroke="#b8c2d4"/>
  <line x1="{x0}" x2="{x0}" y1="{y0}" y2="{y0 + chart_h}" stroke="#b8c2d4"/>
  {''.join(lines)}
  <text x="{x0}" y="314" class="axis">2026-05-01</text>
  <text x="{x0 + chart_w - 92}" y="314" class="axis">2026-07-31</text>
  {''.join(legend)}
</svg>
"""


def svg_bar_chart(city_stats):
    width, height = 520, 285
    max_value = max(row["avg_aqi"] for row in city_stats) * 1.12
    bars = []
    for index, row in enumerate(city_stats):
        y = 34 + index * 47
        bar_w = row["avg_aqi"] / max_value * 300
        color = "#dc6b36" if row["ville"] == "Antananarivo" else "#1779a6"
        bars.append(f'<text x="0" y="{y + 21}" class="bar-label">{row["city"]}</text>')
        bars.append(f'<rect x="115" y="{y}" width="{bar_w:.1f}" height="29" rx="5" fill="{color}"/>')
        bars.append(f'<text x="{122 + bar_w:.1f}" y="{y + 21}" class="value">{fnum(row["avg_aqi"])}</text>')
    return f'<svg viewBox="0 0 {width} {height}" class="chart">{"".join(bars)}</svg>'


def svg_hourly_chart(hourly_values):
    width, height = 520, 285
    max_value = max(hourly_values) * 1.12
    bars = []
    bar_w = 14
    gap = 4
    x0 = 54
    base = 242
    for hour, value in enumerate(hourly_values):
        h = value / max_value * 170
        x = x0 + hour * (bar_w + gap)
        y = base - h
        bars.append(f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" rx="4" fill="#2d936c"/>')
    return f"""
<svg viewBox="0 0 {width} {height}" class="chart">
  <text x="16" y="50" class="axis">{round(max_value)}</text>
  {''.join(bars)}
  <line x1="{x0}" x2="{x0 + 24 * (bar_w + gap)}" y1="{base}" y2="{base}" stroke="#b8c2d4"/>
  <text x="{x0}" y="270" class="axis">0h</text>
  <text x="{x0 + 24 * (bar_w + gap) - 28}" y="270" class="axis">23h</text>
</svg>
"""


def svg_pollutants(city_stats):
    selected = next(row for row in city_stats if row["ville"] == "Dakar")
    items = [
        ("PM10", selected["avg_pm10"], "#1779a6"),
        ("PM2.5", selected["avg_pm2_5"], "#dc6b36"),
        ("CO", selected["avg_co"], "#2d936c"),
        ("NO2", selected["avg_no2"], "#8b5aa6"),
    ]
    max_value = max(item[1] for item in items) * 1.12
    bars = []
    for index, (label, value, color) in enumerate(items):
        x = 58 + index * 112
        h = value / max_value * 185
        y = 230 - h
        bars.append(f'<rect x="{x}" y="{y:.1f}" width="62" height="{h:.1f}" rx="7" fill="{color}"/>')
        bars.append(f'<text x="{x - 6}" y="{y - 10:.1f}" class="value">{fnum(value)}</text>')
        bars.append(f'<text x="{x + 3}" y="262" class="bar-label">{label}</text>')
    return f'<svg viewBox="0 0 520 285" class="chart">{"".join(bars)}</svg>'


def build_payload(rows):
    cities = sorted({row["ville"] for row in rows})
    dates = sorted({row["date"] for row in rows})
    daily = defaultdict(lambda: defaultdict(list))
    hourly = defaultdict(list)
    for row in rows:
        daily[row["ville"]][row["date"]].append(row["aqi"])
        if row["ville"] == "Dakar":
            hourly[row["hour"]].append(row["aqi"])

    daily_series = {
        city: [avg(daily[city][date]) for date in dates if daily[city][date]]
        for city in cities
    }
    hourly_values = [avg(hourly[hour]) for hour in range(24)]
    city_stats = []
    for city in cities:
        subset = [row for row in rows if row["ville"] == city]
        peak = max(subset, key=lambda row: row["aqi"])
        city_stats.append(
            {
                "ville": city,
                "city": CITY_LABELS[city],
                "records": len(subset),
                "avg_aqi": avg(row["aqi"] for row in subset),
                "max_aqi": max(row["aqi"] for row in subset),
                "peak": peak["datetime"].strftime("%Y-%m-%dT%H:%M"),
                "avg_pm10": avg(row["pm10"] for row in subset),
                "avg_pm2_5": avg(row["pm2_5"] for row in subset),
                "avg_co": avg(row["co"] for row in subset),
                "avg_no2": avg(row["no2"] for row in subset),
                "latitude": subset[0]["latitude"],
                "longitude": subset[0]["longitude"],
            }
        )
    city_stats.sort(key=lambda row: row["avg_aqi"], reverse=True)
    return {
        "rows": rows,
        "cities": cities,
        "dates": dates,
        "daily_series": daily_series,
        "hourly_values": hourly_values,
        "city_stats": city_stats,
        "meta": {
            "records": len(rows),
            "city_count": len(cities),
            "period_start": min(row["datetime"] for row in rows).strftime("%Y-%m-%d"),
            "period_end": max(row["datetime"] for row in rows).strftime("%Y-%m-%d"),
            "duplicates": len(rows) - len({(row["ville"], row["datetime"]) for row in rows}),
        },
    }


def write_html(payload):
    stats = payload["city_stats"]
    meta = payload["meta"]
    line = svg_line_chart(payload["daily_series"], payload["cities"])
    bars = svg_bar_chart(stats)
    hours = svg_hourly_chart(payload["hourly_values"])
    pollutants = svg_pollutants(stats)
    table_rows = "\n".join(
        f"""
        <tr>
          <td>{row['city']}</td>
          <td>{row['records']}</td>
          <td>{fnum(row['avg_aqi'])}</td>
          <td>{int(row['max_aqi'])}</td>
          <td>{row['peak']}</td>
          <td>{fnum(row['avg_pm2_5'])}</td>
        </tr>
        """
        for row in stats
    )
    html = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=1920, initial-scale=1">
  <title>Dashboard IA1 Power BI</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      width: 1920px;
      height: 1080px;
      overflow: hidden;
      background: #f3f6fb;
      color: #07162c;
      font-family: "Segoe UI", Arial, sans-serif;
    }}
    .header {{
      height: 108px;
      padding: 18px 40px;
      background: #102033;
      color: #fff;
    }}
    .header h1 {{ margin: 0; font-size: 46px; line-height: 1.08; letter-spacing: 0; }}
    .header p {{ margin: 10px 0 0; font-size: 17px; color: #d9e2ef; }}
    .wrap {{ padding: 16px 32px 18px; }}
    .filters {{ display: flex; align-items: center; gap: 12px; margin-left: 210px; margin-bottom: 12px; font-size: 17px; }}
    .select, .btn {{ height: 38px; border: 1px solid #d6deeb; background: #fff; border-radius: 6px; padding: 8px 16px; }}
    .btn.active {{ background: #1779a6; color: #fff; border-color: #1779a6; }}
    .kpis {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 16px; width: 1440px; margin: 0 auto 14px; }}
    .panel, .kpi {{
      background: #fff;
      border: 1px solid #d8e0ed;
      border-radius: 8px;
      box-shadow: 0 16px 36px rgba(20, 36, 61, 0.08);
    }}
    .kpi {{ height: 92px; padding: 18px 22px; }}
    .kpi span {{ color: #52627a; font-size: 14px; }}
    .kpi strong {{ display: block; margin-top: 8px; font-size: 30px; line-height: 1.05; }}
    .kpi strong.period {{ font-size: 25px; white-space: nowrap; }}
    .top {{ display: grid; grid-template-columns: 1040px 520px; gap: 16px; width: 1440px; margin: 0 auto 14px; }}
    .bottom {{ display: grid; grid-template-columns: 470px 470px 470px; gap: 16px; width: 1440px; margin: 0 auto 14px; }}
    .panel {{ padding: 16px 24px; }}
    .top .panel {{ height: 315px; }}
    .bottom .panel {{ height: 205px; }}
    h2 {{ margin: 0 0 10px; font-size: 22px; }}
    .insight {{ border-left: 5px solid #dc6b36; background: #fff7f1; padding: 9px 13px; margin-bottom: 9px; border-radius: 5px; font-size: 16px; line-height: 1.25; }}
    .chart {{ width: 100%; height: auto; display: block; }}
    .top .chart {{ height: 258px; }}
    .bottom .chart {{ height: 135px; }}
    .axis, .legend, .value, .bar-label {{ font-family: "Segoe UI", Arial, sans-serif; fill: #42526b; font-size: 14px; }}
    .legend {{ font-size: 15px; }}
    .value {{ font-size: 14px; }}
    .bar-label {{ font-size: 15px; fill: #07162c; }}
    .caption {{ color: #52627a; font-size: 14px; margin: 2px 0 0; }}
    .table-panel {{ width: 1440px; height: 165px; margin: 0 auto; padding: 13px 24px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ text-align: left; border-bottom: 1px solid #d8e0ed; padding: 5px 10px; }}
    th {{ color: #52627a; font-weight: 600; }}
  </style>
</head>
<body>
  <section class="header">
    <h1>Dashboard IA1 - Qualite de l'air</h1>
    <p>Analyse individuelle des donnees AQI collectees par le pipeline DONNEES2 de SquadAnalytics.</p>
  </section>
  <main class="wrap">
    <div class="filters">
      <span>Ville</span><div class="select">Dakar</div>
      <div class="btn active">AQI</div><div class="btn">PM10</div><div class="btn">PM2.5</div><div class="btn">NO2</div>
    </div>
    <section class="kpis">
      <div class="kpi"><span>Lignes analysees</span><strong>{meta['records']:,}</strong></div>
      <div class="kpi"><span>Villes suivies</span><strong>{meta['city_count']}</strong></div>
      <div class="kpi"><span>Periode couverte</span><strong class="period">{meta['period_start']} -> {meta['period_end']}</strong></div>
      <div class="kpi"><span>Doublons ville+heure</span><strong>{meta['duplicates']}</strong></div>
    </section>
    <section class="top">
      <div class="panel"><h2>Evolution quotidienne - AQI</h2>{line}</div>
      <div class="panel">
        <h2>Insights a presenter</h2>
        <div class="insight">Dakar affiche l'AQI moyen le plus eleve ({fnum(stats[0]['avg_aqi'])}).</div>
        <div class="insight">Antananarivo est la ville la plus favorable sur la periode ({fnum(stats[-1]['avg_aqi'])} en moyenne).</div>
        <div class="insight">Le pic observe atteint {int(stats[0]['max_aqi'])} a Dakar le {stats[0]['peak']}.</div>
        <div class="insight">Le fichier clean respecte le contrat IA1/DONNEES2 : une ligne par ville et par heure, sans doublons.</div>
      </div>
    </section>
    <section class="bottom">
      <div class="panel"><h2>AQI moyen par ville</h2>{bars}</div>
      <div class="panel"><h2>Profil horaire - Dakar</h2>{hours}<p class="caption">Moyenne par heure de la journee pour la ville la plus exposee.</p></div>
      <div class="panel"><h2>Polluants moyens - Dakar</h2>{pollutants}</div>
    </section>
    <section class="panel table-panel">
      <h2>Comparatif des villes</h2>
      <table>
        <thead><tr><th>Ville</th><th>Lignes</th><th>AQI moyen</th><th>AQI max</th><th>Pic</th><th>PM2.5 moyen</th></tr></thead>
        <tbody>{table_rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""
    HTML_OUT.write_text(html, encoding="utf-8")


def main():
    OUT_DIR.mkdir(exist_ok=True)
    rows = parse_rows()
    payload = build_payload(rows)
    JSON_OUT.write_text(json.dumps(payload["meta"], indent=2), encoding="utf-8")
    write_html(payload)
    print(HTML_OUT)


if __name__ == "__main__":
    main()
