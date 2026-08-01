# Script presentation IA1 - Qualite de l'air

Objectif : presenter le dashboard en moins de 3 minutes.

## 0:00 - 0:25 | Introduction

Bonjour, je presente mon dashboard IA1 sur la qualite de l'air.  
Les donnees viennent du pipeline DONNEES2 de SquadAnalytics et couvrent 5 villes : Antananarivo, Dakar, New York, Paris et Tokyo.

La periode analysee va du 2026-05-01 au 2026-07-31. Le fichier contient 11 005 lignes propres, avec 0 doublon ville-heure.

## 0:25 - 1:10 | Vue generale

Sur la page 3, on voit les indicateurs principaux :
- nombre de lignes analysees ;
- nombre de villes suivies ;
- periode couverte ;
- controle des doublons.

Le graphique principal montre l'evolution quotidienne de l'AQI par ville. Il permet de comparer les tendances et les pics de pollution sur la periode.

Pendant la video, utiliser le filtre `ville_key` : selectionner Dakar pour montrer que les graphiques se mettent a jour, puis revenir a `Tout` pour afficher toutes les villes.

## 1:10 - 2:05 | Insights importants

Le premier insight est que Dakar affiche l'AQI moyen le plus eleve, environ 82,03.  
Cela signifie que Dakar est la ville la plus exposee dans ce jeu de donnees.

Antananarivo est la ville la plus favorable, avec un AQI moyen autour de 24,59.  
Le pic maximal observe atteint 181 a Dakar le 2026-05-17 a 09:00.

Le graphique AQI moyen par ville confirme ce classement : Dakar est nettement au-dessus des autres villes.

## 2:05 - 2:45 | Analyse complementaire

Le profil horaire permet de presenter la variation pendant la journee pour Dakar.  
Le comparatif des villes resume les lignes, l'AQI moyen, l'AQI maximal et le moment du pic.

Cette structure permet donc de passer rapidement d'une vue globale a une analyse detaillee par ville.

## 2:45 - 3:00 | Conclusion

En conclusion, le dashboard montre que les donnees sont propres et exploitables.  
L'analyse met surtout en evidence Dakar comme ville la plus critique, tandis qu'Antananarivo presente les meilleurs niveaux moyens sur la periode.

## Fichiers a rendre

- Power BI : `ia1_powerbi/IA1_dashboard_aqi.pbix`
- Notebook : `ia1/IA1_analyse_aqi.ipynb`
- Capture si pas de lien public : `ia1_powerbi/captures/capture_dashboard_ia1_page3.png`
