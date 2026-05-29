import requests
import os

def optimiser_et_fusionner():
    URL_PACHA = "https://raw.githubusercontent.com/Pacha-droid/playlist-iptv/main/playlist.m3u"
    FICHIER_LOCAL = "ma_playlist.m3u"
    FICHIER_SORTIE = "playlist_finale.m3u"
    
    # --- CONFIGURATION DE LA MISE À JOUR ---
    # Si l'IP '151.80.18.177:86' change un jour, il suffira de modifier la ligne NOUVELLE_IP
    IP_ACTUELLE = "151.80.18.177:86"
    NOUVELLE_IP = "151.80.18.177:86" 
    
    TOKEN_SPORT = "" 
    
    lignes_finales = ["#EXTM3U\n"]
    
    print("⏳ Traitement de votre playlist locale...")
    if os.path.exists(FICHIER_LOCAL):
        with open(FICHIER_LOCAL, "r", encoding="utf-8") as f:
            lignes = f.readlines()
            
        for i in range(len(lignes)):
            ligne = lignes[i].strip()
            if ligne.startswith("#EXTINF"):
                # Correction automatique des groupes mal configurés
                if 'group-title="#EXTM3U"' in ligne:
                    if "sport" in ligne.lower() or "eurosport" in ligne.lower() or "golf" in ligne.lower():
                        ligne = ligne.replace('group-title="#EXTM3U"', 'group-title="Sports"')
                    else:
                        ligne = ligne.replace('group-title="#EXTM3U"', 'group-title="Chaines FR"')
                lignes_finales.append(ligne + "\n")
                
            elif ligne.startswith("http"):
                # Remplacement automatique de l'IP si nécessaire
                ligne_modifiee = ligne.replace(IP_ACTUELLE, NOUVELLE_IP)
                if "stream.m3u8?d=w&id=" in ligne_modifiee and TOKEN_SPORT:
                    ligne_modifiee = ligne_modifiee + TOKEN_SPORT
                lignes_finales.append(ligne_modifiee + "\n")
    else:
        print("⚠️ Fichier local introuvable.")

    print("⏳ Récupération de la playlist distante (Pacha-droid)...")
    try:
        response = requests.get(URL_PACHA, timeout=15)
        if response.status_code == 200:
            lignes_pacha = response.text.splitlines()
            for ligne in lignes_pacha:
                ligne = ligne.strip()
                if ligne and not ligne.startswith("#EXTM3U"):
                    lignes_finales.append(ligne + "\n")
            print("✅ Playlist distante fusionnée.")
        else:
            print(f"❌ Erreur Pacha-droid: Code {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")

    # Écriture du fichier final combiné
    with open(FICHIER_SORTIE, "w", encoding="utf-8") as f:
        f.writelines(lignes_finales)
    print(f"🎉 Terminé ! '{FICHIER_SORTIE}' a été généré avec succès.")

if __name__ == "__main__":
    optimiser_et_fusionner()
