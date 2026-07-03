# Yélo Monitor

Suivi en temps réel de la disponibilité des stations du service de vélos en libre-service **Yélo** dans l'agglomération de La Rochelle.

## Description

Ce projet interroge périodiquement l'API open data de l'Agglo La Rochelle pour récupérer l'état des stations Yélo (vélos disponibles, accroches libres) et génère :
- des cartes interactives (HTML) via Folium
- un historique horodaté au format CSV

Il a été ajouté deux fonctions pour créer des PNG horodatée pour une journée donnée et pour créer un GIF représentant l'évolution de l'occupation des stations stations sur une journée. 


## Fonctionnalités

- Récupération des données via l'API Opendatasoft (`opendata.agglo-larochelle.fr`)
- Calcul des places libres (`accroches_libres = nombre_emplacements - velos_disponibles`)
- Jointure spatiale avec les limites communales (`gpd.sjoin`)
- Cartes proportionnelles avec la couleur Yélo (`#FFDD00`)
- Collecte automatisée sur une plage horaire définie (8h–22h, toutes les 30 min)

## Prérequis

```bash
pip install geopandas matplotlib contextily folium requests pandas
pip install os
pip install requests
pip install csv
pip install datetime
pip install time
pip install logging
pip install cartiflette 
pip install geopandas
pip install contextily 
pip install matplotlib.pyplot
pip install folium
pip install base64
pip install io
pip install shapely.geometry  


## Utilisation

```bash
python yelo_monitoring.py = monitoring avec création CSV hordaté et création carte html 

Les données .CSV sont enregistrées dans le dossier `DATA_CSV`

La carte html est enregistrée dans le dossier 'HTML'

Python generate_png.py permet de générer des PNG pour chaque .CSV (il faut que les CSV soient déjà enregistrés) sur un jour donné.
python creation_gif.py permet de généer un GIF à partir des PNG sur un jour donné.
La date attendue pour PNG et GIF est à renseigner directement dans le code avec la variable date_GIF="02_07_2026"

## Déploiement

Le script peut être planifié via cron ou systemd pour tourner en continu sur un serveur.

Exemple de cron (toutes les 30 minutes, entre 6h et 22h) :
```cron
*/30 6-21 * * * /usr/bin/python3 /chemin/vers/yelo_monitoring.py
```

Des exemples de CSV, PNG et carte HTML sont mis à dispositions. 


## Structure du projet

yelo-monitor/
├── yelo_monitoring.py
├── decoupage_cda_restreint_zoom.geojson
├── velo_disponibilite.geojson
├── DATA/                  
└── README.md


#détails 
Les communes de Angoulins et Chatelaillon ne sont pas représentées dans les PNG par soucis de lisibilité de la carte mais le sont sur la carte interactive HTML.  

Des fichiers pyhtons ont été créé pour justement restreindre le périmètre géographique 

