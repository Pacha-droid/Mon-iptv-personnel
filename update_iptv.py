import requests
import os
import re

def optimiser_et_fusionner():
    FICHIER_LOCAL = "ma_playlist.m3u"
    FICHIER_SORTIE = "playlist_finale.m3u"
    
    # --- CONFIGURATION DE LA MISE À JOUR ---
    IP_ACTUELLE = "151.80.18.177:86"
    NOUVELLE_IP = "151.80.18.177:86" 
    TOKEN_SPORT = "" 
    
    # Signature anti-blocage (Erreur 502)
    USER_AGENT_FORCÉ = "|User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # --- TOUTES TES SOURCES GITHUB AUTOMATIQUES ---
    SOURCES_DISTANTES = {
        "Pacha-droid": "https://raw.githubusercontent.com/Pacha-droid/playlist-iptv/main/playlist.m3u",
        "IPTV_Org_Arab": "https://iptv-org.github.io/iptv/languages/ara.m3u",       # Chaînes Arabes mondiales
        "IPTV_Org_Sports": "https://iptv-org.github.io/iptv/categories/sports.m3u",  # Chaînes de Sport mondiales
        "IPTV_Org_English": "https://iptv-org.github.io/iptv/languages/eng.m3u"     # Chaînes Anglaises (UK/USA)
    }
    
    lignes_finales = ["#EXTM3U\n"]
    
    def attribuer_groupe_intelligent(ligne_extinf):
        """Analyse le nom de la chaîne pour lui attribuer un groupe propre s'il est mal configuré"""
        nom_chaine = ligne_extinf.split(",")[-1].lower() if "," in ligne_extinf else ""
        
        # 1. Détection des chaînes de Sport par Langue
        if any(mot in nom_chaine for mot in ["sport", "bein", "foot", "eurosport", "golf", "canal+", "rmc", "arena", "ssc"]):
            if any(ar in nom_chaine for ar in ["ar", "arabic", "arab", "بين", "الكأس"]):
                return 'group-title="Sports AR"'
            elif any(en in nom_chaine for en in ["en", "uk", "us", "usa", "english"]):
                return 'group-title="Sports EN"'
            elif any(es in nom_chaine for es in ["es", "esp", "spain"]):
                return 'group-title="Sports ES"'
            else:
                return 'group-title="Sports FR"'
        
        # 2. Détection des chaînes généralistes Arabes ou Internationales
        elif any(ar in nom_chaine for ar in ["ar:", "arabic", "mbc", "rotana", "al jazeera", "news"]):
            return 'group-title="Chaines AR"'
        elif any(en in nom_chaine for en in ["en:", "sky", "bbc"]):
            return 'group-title="Chaines EN"'
            
        # 3. Groupe par défaut pour le reste
        return 'group-title="Chaines FR"'

    # --- 1. TRAITEMENT DU FICHIER LOCAL ---
    print("⏳ Traitement de votre playlist locale...")
    if os.path.exists(FICHIER_LOCAL):
        with open(FICHIER_LOCAL, "r", encoding="utf-8") as f:
            lignes = f.readlines()
            
        for i in range(len(lignes)):
            ligne = lignes[i].strip()
            if ligne.startswith("#EXTINF"):
                if 'group-title="#EXTM3U"' in ligne or 'group-title=""' in ligne or 'group-title=' not in ligne:
                    nouveau_groupe = attribuer_groupe_intelligent(ligne)
                    if 'group-title=' in ligne:
                        ligne = re.sub(r'group-title="[^"]*"', nouveau_groupe, ligne)
                    else:
                        ligne = ligne.replace(',', f' {nouveau_groupe},')
                lignes_finales.append(ligne + "\n")
                
            elif ligne.startswith("http"):
                ligne_modifiee = ligne.replace(IP_ACTUELLE, NOUVELLE_IP)
                if "stream.m3u8?d=w&id=" in ligne_modifiee and TOKEN_SPORT:
                    ligne_modifiee = ligne_modifiee + TOKEN_SPORT
                if "|User-Agent=" not in ligne_modifiee:
                    ligne_modifiee = ligne_modifiee + USER_AGENT_FORCÉ
                lignes_finales.append(ligne_modifiee + "\n")
    else:
        print("⚠️ Fichier local introuvable.")

    # --- 2. RÉCUPÉRATION DES PLAYLISTS DISTANTES ---
    for nom_source, url in SOURCES_DISTANTES.items():
        print(f"⏳ Récupération et filtrage de : {nom_source}...")
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                lignes_distantes = response.text.splitlines()
                for i in range(len(lignes_distantes)):
                    ligne = lignes_distantes[i].strip()
                    
                    if ligne.startswith("#EXTINF"):
                        # Force le tri intelligent sur les groupes importés
                        nouveau_groupe = attribuer_groupe_intelligent(ligne)
                        if 'group-title=' in ligne:
                            ligne = re.sub(r'group-title="[^"]*"', nouveau_groupe, ligne)
                        else:
                            ligne = ligne.replace(',', f' {nouveau_groupe},')
                        lignes_finales.append(ligne + "\n")
                        
                    elif ligne.startswith("http"):
                        if "|User-Agent=" not in ligne:
                            ligne = ligne + USER_AGENT_FORCÉ
                        lignes_finales.append(ligne + "\n")
                        
                print(f"✅ {nom_source} fusionnée et triée.")
            else:
                print(f"❌ Erreur {nom_source}: Code {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur de connexion sur {nom_source} : {e}")

    # Écriture du fichier final combiné
    with open(FICHIER_SORTIE, "w", encoding="utf-8") as f:
        f.writelines(lignes_finales)
    print(f"🎉 Terminé ! '{FICHIER_SORTIE}' a fusionné toutes les sources avec succès.")

if __name__ == "__main__":
    optimiser_et_fusionner()

