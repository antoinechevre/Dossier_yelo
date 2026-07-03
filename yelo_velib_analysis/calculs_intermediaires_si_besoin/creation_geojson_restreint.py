import csv
import geopandas as gpd
import os
import matplotlib.pyplot as plt


# chemins répertoire du script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
chemin_csv=os.path.join(BASE_DIR,"DATA","yelo_station.csv") #chemin csv ref yelo
chemin_csv_decoupage=os.path.join(BASE_DIR,"DATA","decoupage_cda.csv") #chemin csv ref contours communes
chemin_geojson_decoupage=os.path.join(BASE_DIR,"DATA","decoupage_cda.geojson") #chemin geojson contours communes
chemin_geojson_stations=os.path.join(BASE_DIR,"DATA","velo_disponibilite.geojson") #chemin geojson stations yelo 


agglo_lr = gpd.read_file(chemin_geojson_decoupage)
station_yelo_data=gpd.read_file(chemin_geojson_stations)


# vérification et alignement des CRS
print("CRS agglo:", agglo_lr.crs)
print("CRS stations:", station_yelo_data.crs)

if agglo_lr.crs != station_yelo_data.crs:
    station_yelo_data = station_yelo_data.to_crs(agglo_lr.crs)

# reprojection en Web Mercator pour compatibilité avec contextily
agglo_lr = agglo_lr.to_crs(epsg=3857)
station_yelo_data = station_yelo_data.to_crs(epsg=3857)

# périmètre restreint 

perimetre_restreint = gpd.sjoin(
    station_yelo_data, 
    agglo_lr,
    how = 'inner',
    predicate="within"
    
)

# liste des codes_insee des communes où il y a au moins une station
codes_communes_avec_station = perimetre_restreint["code_insee"].unique()

agglo_lr_restreint = agglo_lr[agglo_lr["code_insee"].isin(codes_communes_avec_station)]

chemin_sortie = os.path.join(BASE_DIR, "DATA", "decoupage_cda_restreint.geojson")

agglo_lr_restreint.to_file(chemin_sortie, driver="GeoJSON")


