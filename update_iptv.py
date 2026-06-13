import re
import requests

def collecter_flux():
    # Lien absolu vers votre fichier global en désordre
    url_source = "https://raw.githubusercontent.com/Pacha-droid/Mon-iptv-personnel/main/playlist_finale.m3u"
    
    # Liste ultra-complète pour ne rater aucun match de la Coupe du Monde 2026
    cibles = [
        "m6", "tf1", "bein",                      # Diffuseurs principaux en France
        "coupe du monde", "world cup", "fifa",    # Chaînes thématiques ou événements IPTV
        "rts", "rtbf", "la une", "tipik"          # Diffuseurs gratuits Suisses et Belges (en français)
    ]
    resultats = {}

    try:
        print(f"Téléchargement de la source publique...")
        response = requests.get(url_source, timeout=15)
        response.raise_for_status()
        
        lignes = response.text.split('\n')
        regex_url = r'(http[s]?://[^\s^\"]+\.(?:m3u8|ts|mpd|m3u))'
        
        for idx, ligne in enumerate(lignes):
            if any(cible in ligne.lower() for cible in cibles):
                for j in range(idx + 1, min(idx + 4, len(lignes))):
                    match = re.search(regex_url, lignes[j])
                    if match:
                        url_flux = match.group(1)
                        resultats[ligne] = url_flux
                        break
        return resultats
    except Exception as e:
        print(f"Alerte réseau : {e}")
        return resultats

def ecrire_playlist(donnees):
    fichier_cible = "playlist_mondial.m3u"
    try:
        with open(fichier_cible, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            if not donnees:
                f.write("#EXTINF:-1, -- Flux en attente de mise a jour --\n")
                f.write("http://example.com\n")
            else:
                for meta, url in donnees.items():
                    f.write(f"{meta}\n{url}\n")
        print(f"Fichier {fichier_cible} mis à jour.")
    except IOError as e:
        print(f"Erreur d'écriture : {e}")

if __name__ == "__main__":
    flux_trouves = collecter_flux()
    ecrire_playlist(flux_trouves)


    

