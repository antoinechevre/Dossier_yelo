from PIL import Image
import glob
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Remonte d'un niveau depuis scripts/

# récupération de tous les PNG dans l'ordre chronologique (noms triés par timecode)
chemin_pngs = sorted(glob.glob(os.path.join(BASE_DIR, "PNG", "*.png")))

frames = [Image.open(png) for png in chemin_pngs]

frames[0].save(
    os.path.join(BASE_DIR, "GIF", "evolution_yelo.gif"),
    save_all=True,
    append_images=frames[1:],
    duration=1000,   # durée d'affichage de chaque image en millisecondes
    loop=0,         # 0 = boucle infinie
)
