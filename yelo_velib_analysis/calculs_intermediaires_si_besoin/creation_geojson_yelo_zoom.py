import csv
import geopandas as gpd
import os
import matplotlib.pyplot as plt


# chemins répertoire du script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
chemin_geojson_decoupage = os.path.join(BASE_DIR, "DATA", "decoupage_cda_restreint_zoom_filtre.geojson")  # chemin geojson contours communes
chemin_geojson_stations = os.path.join(BASE_DIR, "DATA", "velo_disponibilite.geojson")  # chemin geojson stations yelo

agglo_lr = gpd.read_file(chemin_geojson_decoupage)
station_yelo_data = gpd.read_file(chemin_geojson_stations)


# vérification et alignement des CRS
print("CRS agglo:", agglo_lr.crs)
print("CRS stations:", station_yelo_data.crs)

if agglo_lr.crs != station_yelo_data.crs:
    station_yelo_data = station_yelo_data.to_crs(agglo_lr.crs)

# reprojection en Web Mercator pour compatibilité avec contextily
agglo_lr = agglo_lr.to_crs(epsg=3857)
station_yelo_data = station_yelo_data.to_crs(epsg=3857)

# périmètre restreint

perimetre_restreint_station = gpd.sjoin(
    station_yelo_data,
    agglo_lr,
    how='inner',
    predicate="within"
)

print(perimetre_restreint_station)

perimetre_restreint_station.info()


# filtrage de station_yelo_data à partir des index conservés par le sjoin
# (le sjoin garde l'index d'origine du GeoDataFrame "left", ici station_yelo_data)
station_yelo_zoom = station_yelo_data.loc[perimetre_restreint_station.index.unique()]

chemin_sortie = os.path.join(BASE_DIR, "DATA", "velo_disponibilite_zoom.geojson")

station_yelo_zoom.to_file(chemin_sortie, driver="GeoJSON")

print(station_yelo_zoom)