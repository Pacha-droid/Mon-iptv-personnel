import requests
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIGURATION DU TESTEUR ---
# ⚠️ METS "True" UNIQUEMENT si tu veux tester la validité des liens en ligne.
# ⚠️ METS "False" pour simplement fusionner, nettoyer les doublons et TOUT TRIER par catégorie sans risquer de blocage.
VERIFIER_LES_LIENS = False  

MAX_THREADS = 30         
TIMEOUT_CONNEXION = 5.0  # Augmenté à 5 secondes pour être plus tolérant

def optimiser_et_fusionner():
    FICHIER_LOCAL = "ma_playlist.m3u"
    FICHIER_SORTIE = "playlist_finale.m3u"
    
    IP_ACTUELLE = "151.80.18.177:86"
    NOUVELLE_IP = "151.80.18.177:86" 
    TOKEN_SPORT = "" 
    
    USER_AGENT_FORCÉ = "|User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    SOURCES_STABLES = {
        "Pacha-droid": "https://raw.githubusercontent.com/Pacha-droid/playlist-iptv/main/playlist.m3u",
        "Free_TV_Global": "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
        "Pluto_TV_FR": "https://i.mjh.nz/PlutoTV/fr.m3u8"
    }

    SOURCES_TEMPORAIRES = {
        "Daily_Auto_Sport": "https://raw.githubusercontent.com/FazzR9/IPTV-Daily/master/Sport.m3u",
        "StaySane_Daily": "https://raw.githubusercontent.com/StaySaneApp/Daily-IPTV/main/sport.m3u",
        "Arab_Daily_Channels": "https://iptv-org.github.io/iptv/languages/ara.m3u"
    }
    
    TOUTES_SOURCES = {**SOURCES_STABLES, **SOURCES_TEMPORAIRES}
    
    candidats_chaines = []
    lignes_finales = ["#EXTM3U\n"]
    urls_uniques_detection = set()

    def attribuer_groupe_intelligent(ligne_extinf):
        nom_chaine = ligne_extinf.split(",")[-1].lower() if "," in ligne_extinf else ""
        if any(mot in nom_chaine for mot in ["sport", "bein", "foot", "eurosport", "golf", "canal+", "rmc", "arena", "ssc", "alkass"]):
            if any(ar in nom_chaine for ar in ["ar", "arabic", "arab", "بين", "الكأس", "ssc"]):
                return 'group-title="Sports AR"'
            elif any(en in nom_chaine for en in ["en", "uk", "us", "usa", "english"]):
                return 'group-title="Sports EN"'
            elif any(es in nom_chaine for es in ["es", "esp", "spain"]):
                return 'group-title="Sports ES"'
            else:
                return 'group-title="Sports FR"'
        elif any(ar in nom_chaine for ar in ["ar:", "arabic", "mbc", "rotana", "al jazeera", "news", "アル"]):
            return 'group-title="Chaines AR"'
        elif any(en in nom_chaine for en in ["en:", "sky", "bbc"]):
            return 'group-title="Chaines EN"'
        return 'group-title="Chaines FR"'

    def extraire_nom_pur(ligne_extinf):
        if "," in ligne_extinf:
            return ligne_extinf.split(",")[-1].strip().upper()
        return ligne_extinf.strip().upper()

    def verifier_un_flux(item):
        extinf, url_complete = item
        if not VERIFIER_LES_LIENS:
            return extinf, url_complete
            
        url_pure = url_complete.split('|')[0].strip()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        try:
            # verify=False ignore les erreurs de certificats SSL obsolètes des serveurs IPTV
            with requests.get(url_pure, headers=headers, timeout=TIMEOUT_CONNEXION, stream=True, verify=False) as r:
                if r.status_code in [200, 206, 302]:
                    return extinf, url_complete
        except Exception:
            pass
        return None

    # --- ÉTAPE 1 : LECTURE DU FICHIER LOCAL ---
    print("⏳ Analyse de votre playlist locale...")
    if os.path.exists(FICHIER_LOCAL):
        with open(FICHIER_LOCAL, "r", encoding="utf-8") as f:
            lignes = f.readlines()
            
        extinf_temp = None
        for ligne in lignes:
            ligne = ligne.strip()
            if ligne.startswith("#EXTINF"):
                nouveau_groupe = attribuer_groupe_intelligent(ligne)
                if 'group-title=' in ligne:
                    ligne = re.sub(r'group-title="[^"]*"', nouveau_groupe, ligne)
                else:
                    ligne = ligne.replace(',', f' {nouveau_groupe},', 1) # 1 seul remplacement max !
                extinf_temp = ligne
            elif ligne.startswith("http") and extinf_temp:
                ligne_modifiee = ligne.replace(IP_ACTUELLE, NOUVELLE_IP)
                if "stream.m3u8?d=w&id=" in ligne_modifiee and TOKEN_SPORT:
                    ligne_modifiee += TOKEN_SPORT
                if "|User-Agent=" not in ligne_modifiee:
                    ligne_modifiee += USER_AGENT_FORCÉ
                
                if ligne_modifiee not in urls_uniques_detection:
                    urls_uniques_detection.add(ligne_modifiee)
                    candidats_chaines.append((extinf_temp, ligne_modifiee))
                extinf_temp = None

    # --- ÉTAPE 2 : DOSSIER DES SOURCES DISTANTES ---
    for nom_source, url in TOUTES_SOURCES.items():
        print(f"⏳ Aspiration de la source : {nom_source}...")
        try:
            response = requests.get(url, timeout=12, verify=False)
            if response.status_code == 200:
                lignes_distantes = response.text.splitlines()
                extinf_temp = None
                for ligne in lignes_distantes:
                    ligne = ligne.strip()
                    if ligne.startswith("#EXTINF"):
                        nouveau_groupe = attribuer_groupe_intelligent(ligne)
                        if 'group-title=' in ligne:
                            ligne = re.sub(r'group-title="[^"]*"', nouveau_groupe, ligne)
                        else:
                            ligne = ligne.replace(',', f' {nouveau_groupe},', 1)
                        extinf_temp = ligne
                    elif ligne.startswith("http") and extinf_temp:
                        if "|User-Agent=" not in ligne:
                            ligne += USER_AGENT_FORCÉ
                        
                        if ligne not in urls_uniques_detection:
                            urls_uniques_detection.add(ligne)
                            candidats_chaines.append((extinf_temp, ligne))
                        extinf_temp = None
        except Exception:
            print(f"❌ Impossible de joindre la source distante : {nom_source}")

    # --- ÉTAPE 3 : FILTRAGE ET FILTRE MULTI-THREADÉ ---
    total_liens = len(candidats_chaines)
    chaines_valides_brutes = []
    
    if VERIFIER_LES_LIENS:
        print(f"\n🚀 Lancement de la vérification en direct sur {total_liens} flux...")
        compteur = 0
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = {executor.submit(verifier_un_flux, item): item for item in candidats_chaines}
            for future in as_completed(futures):
                compteur += 1
                resultat = future.result()
                if resultat:
                    chaines_valides_brutes.append(resultat)
                if compteur % 100 == 0 or compteur == total_liens:
                    print(f"🔄 Analyse : {compteur}/{total_liens} liens testés...")
    else:
        print(f"\n⚡ Mode rapide : Intégration directe de {total_liens} flux sans vérification en ligne.")
        chaines_valides_brutes = candidats_chaines

    # --- ÉTAPE 4 : DÉDUPLICATION STRICTE ---
    print("\n🧹 Nettoyage des doublons...")
    chaines_uniques_finales = []
    cles_chaines_vues = set()

    for extinf, url in chaines_valides_brutes:
        nom_pur = extraire_nom_pur(extinf)
        match_groupe = re.search(r'group-title="([^"]+)"', extinf)
        groupe = match_groupe.group(1) if match_groupe else "Chaines FR"
        
        cle_unique = (nom_pur, groupe)
        
        if cle_unique not in cles_chaines_vues:
            cles_chaines_vues.add(cle_unique)
            chaines_uniques_finales.append((extinf, url))

    # --- ÉTAPE 5 : TRI STRICT PAR CATÉGORIE (Pour IPTV Smarters Pro) ---
    print("🗂️ Tri de la playlist par catégories...")
    
    def extraire_nom_groupe_pour_tri(item):
        extinf, _ = item
        match = re.search(r'group-title="([^"]+)"', extinf)
        return match.group(1) if match else "Chaines FR"

    # Trie les chaînes par ordre alphabétique de leur groupe de chaînes
    chaines_uniques_finales.sort(key=extraire_nom_groupe_pour_tri)

    # --- ÉTAPE 6 : ÉCRITURE ---
    print(f"✍️ Génération finale dans '{FICHIER_SORTIE}'...")
    for extinf, url in chaines_uniques_finales:
        lignes_finales.append(extinf + "\n")
        lignes_finales.append(url + "\n")
        
    with open(FICHIER_SORTIE, "w", encoding="utf-8") as f:
        f.writelines(lignes_finales)
        
    print(f"\n🎉 Terminé ! Ouvrez '{FICHIER_SORTIE}' dans Smarters Pro.")
    print(f"📦 Nombre total de chaînes injectées et ordonnées : {len(chaines_uniques_finales)}")

if __name__ == "__main__":
    optimiser_et_fusionner()



