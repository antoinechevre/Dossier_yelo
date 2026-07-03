import os
import requests
import csv
from datetime import datetime
import time
import logging
from cartiflette import carti_download
import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt
import folium
import base64
import io
from shapely.geometry import shape 
from shapely.geometry import Point
import base64

# chemin absolu du répertoire du script et référencement fichier data et paramètre 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Remonte d'un niveau depuis scripts/
chemin_csv=os.path.join(BASE_DIR,"DATA","yelo_station.csv") #chemin csv ref yelo
chemin_geojson_decoupage=os.path.join(BASE_DIR,"DATA","decoupage_cda_restreint.geojson") #chemin geojson contours communes
chemin_geojson_stations=os.path.join(BASE_DIR,"DATA","velo_disponibilite.geojson") #chemin geojson stations yelo 
chemin_sortie_html = os.path.join(BASE_DIR, "HTML", "carte_yelo.html")

# --- logo encodé une seule fois, hors fonction (évite de relire le fichier à chaque appel) ---
chemin_logo = os.path.join(BASE_DIR, "DATA", "Yelo-Logo-transparent.png")
with open(chemin_logo, "rb") as f:
    LOGO_BASE64 = base64.b64encode(f.read()).decode()

#couleur jaune Yelo pour les camemberts
jaune_yelo = "#FFDD00"
noir_yelo = "#000000"



agglo_lr = gpd.read_file(chemin_geojson_decoupage)
station_yelo_data_ref=gpd.read_file(chemin_geojson_stations)
max_total = station_yelo_data_ref['nombre_emplacements'].max()
date_generation = datetime.now().strftime("%d/%m/%Y")
heure_generation = datetime.now().strftime("%H:%M")

# Configuration
url_serveur = "https://opendata.agglo-larochelle.fr/d4c/api/records/1.0/search/?dataset=yelo___disponibilite_des_velos_en_libre_service&resource_id=1f124bea-d55f-457f-9eab-b7877d803435&facet=station_nom"

# paramètre carto 
TAILLE_MAX = 600

#paramètres temporels 
SLEEP_INTERVAL = 900  # secondes


def is_dans_plage_horaire(heure_debut=8, heure_fin=22):
    heure_actuelle = datetime.now().hour
    return heure_debut <= heure_actuelle < heure_fin

 #Récupère les données en temps réel de l'API Yelo.

def temps_jusqu_a_prochain_creneau(intervalle_minutes=30):
    """Calcule le nombre de secondes à attendre jusqu'au prochain créneau
    aligné sur l'horloge (ex: xx:00 ou xx:30 pour un intervalle de 30 min)."""
    maintenant = datetime.now()
    minutes_ecoulees = maintenant.minute % intervalle_minutes
    secondes_ecoulees = minutes_ecoulees * 60 + maintenant.second + maintenant.microsecond / 1_000_000
    secondes_intervalle = intervalle_minutes * 60
    return secondes_intervalle - secondes_ecoulees

 #Récupère les données en temps réel de l'API Yelo.

def fetch_data():
    try:
        response = requests.get(url_serveur)
        response.raise_for_status()
        if response.status_code == 200:
            print("connexion serveur ok")
        info_reseau = response.json()
        info_stations = info_reseau["records"]

        # Construction des lignes avec géométrie extraite de chaque enregistrement
        rows = []
        for station in info_stations:
            fields = station["fields"]
            lat = fields.get("station_latitude")
            lon = fields.get("station_longitude")
           
            rows.append({
                "Id": fields.get("_id"),
                "station_nom": fields.get("station_nom"),
                "velos_disponibles": fields.get("velos_disponibles"),
                "accroches_libres": fields.get("accroches_libres"),
                "nombre_emplacements": fields.get("nombre_emplacements"),
                "geometry": Point(lon, lat) if lat is not None and lon is not None else None,
            })

        gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
        
        # on écarte les stations sans coordonnées valides (non exploitables sur la carte)
        nb_avant = len(gdf)
        gdf = gdf[gdf.geometry.notna()].reset_index(drop=True)
        nb_ecartees = nb_avant - len(gdf)
        if nb_ecartees > 0:
            print(f"{nb_ecartees} station(s) écartée(s) — coordonnées manquantes")

        return gdf

    except requests.RequestException as e:
        logging.error(f"Erreur lors de la récupération des données: {e}")
        return gpd.GeoDataFrame(
            columns=["Id", "station_nom", "velos_disponibles", "accroches_libres", "nombre_emplacements", "geometry"],
            geometry="geometry",
            crs="EPSG:4326",
        )

#génère timecode horodaté


def timecode(): 
    maintenant=datetime.now()
    date_formatee=maintenant.strftime("%d_%m_%Y") 
    heure_formatee=maintenant.strftime("%H_%M")
    return(date_formatee+"__"+heure_formatee)
    #print(f"date formatée {date_formatee}")
    #print(f"heure formatée {heure_formatee}")

#génère nom fichier csv horodaté

def define_csv_title(): 
    FILENAME=os.path.join(BASE_DIR,"DATA_CSV","yelo"+"__"+timecode()+".csv")
    return(FILENAME)

#génère csv horodaté et csv unique

def save_to_csv(data,FILENAME): 
    os.makedirs(os.path.dirname(FILENAME), exist_ok=True)

    colonnes_export = ["Id", "station_nom", "velos_disponibles", "nombre_emplacements"]
    data_export = data[colonnes_export].copy()
    data_export["timecode jour"] = datetime.now().strftime("%Y-%m-%d")
    data_export["timecode heure"] = datetime.now().strftime("%H:%M:%S")

    # csv horodaté pour historique
    data_export.to_csv(FILENAME, index=False)

    # csv qui se met à jour à chaque relevé
    chemin_csv_unique = os.path.join(BASE_DIR, "DATA", "yelo_station.csv")
    data_export.to_csv(chemin_csv_unique, index=False)

# génère PNG 

def calage_geojson(data, agglo_lr, station_yelo_data):
    # aligne live data + agglo_lr + station_yelo_data statique sur le même CRS
    if data.crs != agglo_lr.crs:
        agglo_lr = agglo_lr.to_crs(data.crs)
    if station_yelo_data.crs != data.crs:
        station_yelo_data = station_yelo_data.to_crs(data.crs)

    data_cale = data.to_crs(epsg=3857)
    agglo_lr_cale = agglo_lr.to_crs(epsg=3857)
    station_yelo_data_cale = station_yelo_data.to_crs(epsg=3857)
    return data_cale, agglo_lr_cale, station_yelo_data_cale

def carte_html(agglo_lr,station_yelo_data): 
    
    #fond de carte OpenStreetMap avec folium, centrée sur l'agglo
    centre = agglo_lr.to_crs(epsg=4326).geometry.union_all().centroid
    m = folium.Map(location=[centre.y, centre.x], zoom_start=13, tiles="OpenStreetMap")

    folium.GeoJson(agglo_lr.to_crs(epsg=4326),style_function=lambda feature: {"color": noir_yelo,"weight": 1.5 ,"fillOpacity": 0.1}).add_to(m)

    stations_4326 = station_yelo_data.to_crs(epsg=4326)

    for idx, row in stations_4326.iterrows():
        valeurs = [row["velos_disponibles"], row["accroches_libres"]]
        rayon = (row["nombre_emplacements"] / max_total) * 20 + 5

    # génération du mini camembert en image
        fig_pie, ax_pie = plt.subplots(figsize=(1, 1))
        if sum(valeurs) == 0:
            ax_pie.pie([1], colors=["lightgrey"])
        else:
            ax_pie.pie(valeurs, colors=[jaune_yelo, noir_yelo])
        ax_pie.set_aspect("equal")

        buf = io.BytesIO()
        fig_pie.savefig(buf, format="png", transparent=True, bbox_inches="tight")
        plt.close(fig_pie)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode()

        icon = folium.CustomIcon(
            icon_image=f"data:image/png;base64,{img_base64}",
            icon_size=(rayon * 2, rayon * 2),
        )
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            icon=icon,
            popup=row["station_nom"],
        ).add_to(m)
        
    # ajout du logo Yélo en haut à droite, fixe par rapport à la fenêtre
    logo_html = f"""
    <div style="
        position: fixed;
        top: 15px;
        right: 15px;
        z-index: 9999;
        width: 80px;
        height: 80px;
    ">
        <img src="data:image/png;base64,{LOGO_BASE64}" style="width:100%; height:100%;">
        </div>
        """
    m.get_root().html.add_child(folium.Element(logo_html))
   
   # ajout de la date et heure du relevé en haut à gauche, fixe par rapport à la fenêtre
   
    date_formatee=datetime.now().strftime("%d_%m_%Y") 
    heure_formatee=datetime.now().strftime("%H_%M") 
    
    date_html = f"""
    <div style="
        position: fixed;
        top: 15px;
        left: 15px;
        z-index: 9999;
        background-color: rgba(255, 255, 255, 0.85);
        padding: 6px 12px;
        border-radius: 6px;
        font-family: Arial, sans-serif;
        font-size: 14px;
        color: #000000;
        box-shadow: 0 1px 4px rgba(0,0,0,0.3);
    ">
        Date {date_formatee} - Heure {heure_formatee} 
    </div>
    """
    m.get_root().html.add_child(folium.Element(date_html))
       
    
    # ajout de la légende (couleurs identiques aux camemberts)
    legende_html = f"""
    <div style="
        position: fixed;
        bottom: 25px;
        left: 15px;
        z-index: 9999;
        background-color: rgba(255, 255, 255, 0.85);
        padding: 8px 14px;
        border-radius: 6px;
        font-family: Arial, sans-serif;
        font-size: 13px;
        color: #000000;
        box-shadow: 0 1px 4px rgba(0,0,0,0.3);
    ">
        <div style="margin-bottom: 4px;">
            <span style="display:inline-block; width:12px; height:12px; background-color:{jaune_yelo}; border-radius:2px; margin-right:6px; vertical-align:middle;"></span>
            Vélos disponibles
        </div>
        <div>
            <span style="display:inline-block; width:12px; height:12px; background-color:{noir_yelo}; border-radius:2px; margin-right:6px; vertical-align:middle;"></span>
            Accroches libres
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legende_html))
    
    # sauvegarde de la carte 
    os.makedirs(os.path.dirname(chemin_sortie_html), exist_ok=True)
    m.save(chemin_sortie_html)
    print("Carte interactive sauvegardée: carte_yelo.html")
    
def main():
    if not is_dans_plage_horaire ():
        print("Hors plage horaire")
        return False # quitte main sans rien faire
    else:
        True 
    data = fetch_data()
    FILENAME=define_csv_title()
    save_to_csv(data,FILENAME)
    print(f"enregistrement du CSV Yelo {timecode()}")
    data_cale, agglo_lr_cale, station_yelo_data_cale = calage_geojson(data, agglo_lr, station_yelo_data_ref)
    carte_html(agglo_lr_cale, data_cale)

if __name__ == "__main__":
    print("création pour `yelo-monitor`.")
    while True: 
        main()
        attente = temps_jusqu_a_prochain_creneau(30)  # 30 minutes
        print(f"prochain relevé dans {attente/60:.1f} minutes")
        time.sleep(SLEEP_INTERVAL)

