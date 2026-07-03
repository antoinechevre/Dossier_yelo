import os
import csv
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox


#chemins répertoire du script

BASE_DIR = os.getcwd()

chemin_dossier_csv = os.path.join(BASE_DIR, "yelo_velib_analysis", "DATA_CSV")
chemin_geojson_stations = os.path.join(BASE_DIR, "yelo_velib_analysis", "DATA", "velo_disponibilite_zoom.geojson")
chemin_geojson_decoupage = os.path.join(BASE_DIR, "yelo_velib_analysis", "DATA", "decoupage_cda_restreint_zoom_filtre.geojson")
chemin_sortie_png_dir = os.path.join(BASE_DIR, "yelo_velib_analysis", "PNG")

print(BASE_DIR)


#données de cadrage d
date_GIF="02_07_2026"
jaune_yelo = "#FFDD00" # velo libre 
noir_yelo = "#000000" # accroches libres 

TAILLE_MAX = 600

agglo_lr = gpd.read_file(chemin_geojson_decoupage)
station_yelo_data_ref = gpd.read_file(chemin_geojson_stations)
station_yelo_data_ref["station_nom"] = station_yelo_data_ref["station_nom"].astype(str)
max_total = station_yelo_data_ref["nombre_emplacements"].max()

# reprojection en Web Mercator UNE SEULE FOIS, hors boucle
agglo_lr_cale = agglo_lr.to_crs(epsg=3857)
station_geom_3857 = station_yelo_data_ref.to_crs(epsg=3857)[["station_nom", "geometry"]]

#charge le logo Yelo pour l'ajouter sur la carte
chemin_logo = os.path.join(BASE_DIR, "yelo_velib_analysis", "DATA", "Yelo-Logo-transparent.png")
logo_img = mpimg.imread(chemin_logo)


#liste les fichiers CSV dans le dossier, filtrés par date_GIF

csv_files = [f for f in os.listdir(chemin_dossier_csv) if date_GIF in f.lower() and f.lower().endswith(".csv")]
os.makedirs(chemin_sortie_png_dir, exist_ok=True)

for filename in csv_files:
    chemin_fichier = os.path.join(chemin_dossier_csv, filename)
    with open(chemin_fichier, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    df = pd.DataFrame(rows)
    if df.empty:
        continue

    df["station_nom"] = df["station_nom"].astype(str)
    df["velos_disponibles"] = pd.to_numeric(df["velos_disponibles"], errors="coerce")
    df["nombre_emplacements"] = pd.to_numeric(df["nombre_emplacements"], errors="coerce")

    # "accroches_libres" n'existe pas dans le CSV source -> on la recalcule
    # (nombre_emplacements = velos_disponibles + accroches_libres)
    if "accroches_libres" in df.columns:
        df["accroches_libres"] = pd.to_numeric(df["accroches_libres"], errors="coerce")
    else:
        df["accroches_libres"] = df["nombre_emplacements"] - df["velos_disponibles"]

    # merge avec la géométrie (déjà reprojetée) pour obtenir toutes les stations de ce relevé
    gdf = df.merge(station_geom_3857, on="station_nom", how="left")
    gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs=station_geom_3857.crs)
    gdf = gdf[gdf.geometry.notna()]

    # --- création du PNG pour ce relevé zoomé sur l'agglo hors Angoulins / Chatelaillon---
    fig, ax = plt.subplots(figsize=(10, 10))
    agglo_lr_cale.boundary.plot(ax=ax, color="steelblue", edgecolor="white", linewidth=0.5)
    timestamp = gdf["timecode heure"].iloc[0] if "timecode heure" in gdf.columns else "inconnu"
    ax.set_title(f"Agglo La Rochelle — stations Yélo - {date_GIF} - {timestamp}")
    ax.axis("off")
    ax.set_xlim(agglo_lr_cale.total_bounds[[0, 2]])
    ax.set_ylim(agglo_lr_cale.total_bounds[[1, 3]])
   # ctx.add_basemap(ax, crs=agglo_lr_cale.crs, source=ctx.providers.OpenStreetMap.Mapnik, zoom=15)
    ctx.add_basemap(ax, crs=agglo_lr_cale.crs, source=ctx.providers.CartoDB.Positron, zoom=15)


    # voile gris semi-transparent sur toute la carte

    #xlim = ax.get_xlim()
    #ylim = ax.get_ylim()

    #voile = mpatches.Rectangle(
    #    (xlim[0], ylim[0]),                  # coin bas-gauche
    #    xlim[1] - xlim[0],                   # largeur
    #    ylim[1] - ylim[0],                   # hauteur
    #    facecolor="grey",
    #    alpha=0.2,                           # transparence du voile (0 = invisible, 1 = opaque)
    #    zorder=2,                            # au-dessus du basemap
    #    linewidth=0
    #)
    #ax.add_patch(voile)


    for idx, row in gdf.iterrows():
        x, y = row.geometry.x, row.geometry.y
        taille = (row["nombre_emplacements"] / max_total) * TAILLE_MAX

        sub_ax = ax.inset_axes(
            [x - taille / 2, y - taille / 2, taille, taille],
            transform=ax.transData
        )
        valeurs = [row["velos_disponibles"], row["accroches_libres"]]

        if any(pd.isna(v) for v in valeurs) or sum(valeurs) == 0:
            sub_ax.pie([1], colors=["lightgrey"])
        else:
            sub_ax.pie(valeurs, colors=[jaune_yelo, noir_yelo])
        sub_ax.set_aspect("equal")
    imagebox = OffsetImage(logo_img, zoom=0.15)  # ajuste zoom pour la taille du logo
    ab = AnnotationBbox(
        imagebox,
        (0.95, 0.95),              # position en haut à droite (coordonnées 0-1)
        xycoords="axes fraction",
        frameon=False,
        box_alignment=(1, 1),      # ancre le coin haut-droit de l'image sur ce point
    )
    ax.add_artist(ab)
    
    ax.legend(
        handles=[
            plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=jaune_yelo, markersize=10, label="Vélos disponibles"),
            plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=noir_yelo, markersize=10, label="Accroches libres"),
        ],
        loc="lower right",
        bbox_to_anchor=(0.98, 0.05),  # (x, y) en coordonnées figure : augmente y pour remonter
        bbox_transform=ax.transAxes,
    )
    
    plt.tight_layout()

    nom_png = filename.replace(".csv", "") + "_carte_yelo.png"
    chemin_sortie_png = os.path.join(chemin_sortie_png_dir, nom_png)
    plt.savefig(chemin_sortie_png, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Carte sauvegardée: {chemin_sortie_png}")
    

