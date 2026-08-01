# Rendu IA1 individuel avec Power BI

## Fichiers a utiliser

- `ia1_powerbi/tables/fact_qualite_air.csv`
- `ia1_powerbi/tables/dim_ville.csv`
- `ia1_powerbi/tables/dim_temps.csv`
- `ia1_powerbi/mesures_powerbi.dax`
- `ia1_powerbi/GUIDE_POWERBI_IA1.md`
- `ia1/IA1_analyse_aqi.ipynb`

Le dashboard doit etre fait dans Power BI Desktop. Le fichier HTML reste seulement un apercu local, il ne remplace pas le rapport Power BI.

## Construction rapide dans Power BI

1. Ouvre Power BI Desktop.
2. Va dans **Obtenir des donnees > Texte/CSV**.
3. Importe les trois CSV du dossier `ia1_powerbi/tables/`.
4. Dans la vue **Modele**, cree les relations:
   - `fact_qualite_air[ville_key]` vers `dim_ville[ville_key]`
   - `fact_qualite_air[temps_key]` vers `dim_temps[temps_key]`
5. Va dans **Modelisation > Nouvelle mesure** et colle les mesures du fichier `ia1_powerbi/mesures_powerbi.dax`.
6. Cree au moins trois pages:
   - Vue globale AQI
   - Comparaison des polluants
   - Analyse horaire
7. Enregistre le rapport sous `ia1_powerbi/IA1_dashboard_aqi.pbix`.

## Script video conseille

1. Presenter la source: 11 005 mesures, 5 villes, periode du 01/05/2026 au 31/07/2026, 0 doublon.
2. Montrer les KPI Power BI: nombre de mesures, villes suivies, jours couverts, AQI moyen.
3. Montrer la courbe AQI par date et expliquer que Dakar est la ville la plus exposee.
4. Montrer le graphique des polluants moyens: PM10, PM2.5, CO, NO2.
5. Montrer l'analyse par heure et les filtres ville/date.
6. Finir par les insights:
   - Dakar a l'AQI moyen le plus eleve, environ 82.
   - Antananarivo a l'AQI moyen le plus faible, environ 24,6.
   - Le pic observe atteint 181 a Dakar le 17 mai 2026 a 09h.

## Email de rendu

Destinataire: `evaluation@databridge.mg`

Objet: `IA1 - STD - Livrables`

Contenu a adapter:

```text
Bonjour,

Veuillez trouver ci-joint mes livrables pour le projet IA1 individuel:
- la video de presentation du dashboard Power BI;
- le fichier Power BI .pbix, ou les captures d'ecran du dashboard;
- le fichier notebook utilise pour l'analyse.

Nom: [TON NOM]
STD: [TON STD]
Dashboard: [LIEN PUBLIC POWER BI OU mention: fichier PBIX/captures jointes]
Notebook: IA1_analyse_aqi.ipynb

Cordialement,
```
