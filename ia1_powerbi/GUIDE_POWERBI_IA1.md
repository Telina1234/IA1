# IA1 Power BI - Guide de realisation

## Source de donnees

- Projet: SquadAnalytics DONNEES2
- Fichier source: `data/clean/clean.csv`
- Tables Power BI pretes: `ia1_powerbi/tables/`
- Rapport Power BI cree: `ia1_powerbi/IA1_dashboard_aqi.pbix`
- Periode: `2026-05-01T00:00` a `2026-07-31T16:00`
- Lignes: `11005`
- Villes: `Antananarivo, Dakar, New York, Paris, Tokyo`
- Doublons ville + heure: `0`

## Etat du fichier Power BI

Le fichier `IA1_dashboard_aqi.pbix` contient deja une page de rapport avec:

- un graphique comparatif `AQI moyen par ville_key`;
- un graphique AQI par annee et ville, exploitable pour presenter la comparaison entre villes;
- les tables `dim_temps`, `dim_ville` et `fact_qualite_air` chargees dans Power BI;
- les mesures `AQI moyen` et `PM10 moyen`.

Pour une video courte, cette page suffit a presenter les insights principaux. Si tu veux enrichir avant rendu, ajoute une page supplementaire avec les mesures du fichier `mesures_powerbi.dax`.

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
