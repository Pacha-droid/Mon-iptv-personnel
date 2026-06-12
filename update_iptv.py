import re
import requests

def chercher_liens_mondial():
    # URL de la source IPTV publique francophone
    url_source = "https://githubusercontent.com"
    
        # Mots-clés des diffuseurs officiels + chaînes de secours permanentes
    filtres_diffuseurs = {
        "M6 (France)": ["m6", "metropole6"],
        "ARD (Allemagne)": ["ard", "das erste", "sportschau"],
        "ZDF (Allemagne)": ["zdf"],
        "BBC (Royaume-Uni)": ["bbc one", "bbc two", "bbc1", "bbc2"],
        "ITV (Royaume-Uni)": ["itv1", "itv2", "itv channel"],
        "RTVE (Espagne)": ["la 1", "tve1", "rtve"],
        "RAI (Italie)": ["rai 1", "rai uno", "rai sport"],
        "TRT (Turquie)": ["trt 1", "trt spor"],
        "beIN Open (MENA)": ["bein sports", "bein sports open"],
        "France 2 (Secours)": ["france 2", "france2"],
        "TV5 Monde (Secours)": ["tv5", "tv5monde"]
    }


    try:
        print(f"[+] Connexion à la source : {url_source}")
        response = requests.get(url_source, timeout=15)
        response.raise_for_status()
        
        regex_liens = r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\.(?:m3u8|ts|mpd|m3u))'
        lignes = response.text.split('\n')
        resultats = {}
        
        for idx, ligne in enumerate(lignes):
            for chaine, mots_cles in filtres_diffuseurs.items():
                if any(mot in ligne.lower() for mot in mots_cles):
                    for j in range(idx + 1, min(idx + 4, len(lignes))):
                        lien_match = re.search(regex_liens, lignes[j])
                        if lien_match:
                            url_flux = lien_match.group(1)
                            if chaine not in resultats:
                                resultats[chaine] = []
                            if url_flux not in resultats[chaine]:
                                resultats[chaine].append(url_flux)
                            break
        return resultats
    except Exception as e:
        print(f"[-] Erreur : {e}")
        return {}

def generer_fichier_m3u(flux_trouves):
    nom_fichier = "playlist_mondial.m3u"
    try:
        with open(nom_fichier, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            if not flux_trouves:
                # Ligne de secours pour forcer Git à détecter et afficher le fichier
                f.write('#EXTINF:-1, -- En attente de flux Coupe du Monde --\n')
                f.write('http://example.com\n')
            else:
                for chaine, liens in flux_trouves.items():
                    for lien in liens:
                        f.write(f'#EXTINF:-1 tvg-name="{chaine}" group-title="Coupe du Monde 2026", {chaine}\n')
                        f.write(f"{lien}\n")
        print(f"[+] Fichier {nom_fichier} généré avec succès.")
    except Exception as e:
        print(f"[-] Erreur lors de l'écriture du fichier : {e}")





if __name__ == "__main__":
    flux = chercher_liens_mondial()
    # On force la génération du fichier même si la liste est vide pour éviter le bug de GitHub
    generer_fichier_m3u(flux)
    

