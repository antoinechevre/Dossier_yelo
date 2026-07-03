import geopandas as gpd
import json
from pathlib import Path
import os


# Chemins des fichiers
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
fichier_entree = os.path.join(BASE_DIR,"DATA","decoupage_cda_restreint_zoom.geojson")
fichier_sortie = os.path.join(BASE_DIR,"DATA","decoupage_cda_restreint_zoom_filtre.geojson")

# Noms des communes à exclure (attention à l'orthographe exacte utilisée dans le geojson)
communes_a_supprimer = {"Angoulins", "Chatelaillon-Plage"}

# Chargement du geojson
with open(fichier_entree, "r", encoding="utf-8") as f:
    data = json.load(f)

# Filtrage des features : on garde seulement celles dont la commune n'est pas à supprimer
data["features"] = [
    feature for feature in data["features"]
    if feature["properties"]["nom_commune"] not in communes_a_supprimer
]

# Sauvegarde du résultat
with open(fichier_sortie, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"{len(data['features'])} communes restantes après filtrage.")
print(f"Fichier sauvegardé : {fichier_sortie}")


